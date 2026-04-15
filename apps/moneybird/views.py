import json
from datetime import datetime
from urllib.parse import unquote

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, DeleteView, CreateView, UpdateView, View
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView

from apps.moneybird.defaults import make_orderline, make_order
from apps.moneybird.forms import FileForm, ProductForm, ConceptOrderDrinkForm, ConceptOrderDrinkLineForm
from apps.moneybird.tools_moneybird import MoneybirdOrderLine, MoneybirdOrder, Moneybird
from apps.util.profiling import profile
import settings
from .models import Settings, Customer, Product, ConceptOrder, ConceptOrderDrink, ConceptOrderDrinkLine


class Index(LoginRequiredMixin, ListView):
    queryset = ConceptOrder.objects.all().prefetch_related('conceptorderdrink_set')

    def get_context_data(self, **kwargs):
        context = super(Index, self).get_context_data(**kwargs)

        context['create_order_form'] = FileForm()

        context['new_products'] = Product.objects.filter(Q(moneybird_id__isnull=True) | Q(moneybird_id__exact=""))
        context['new_customers'] = Customer.objects.filter(Q(moneybird_id__isnull=True) | Q(moneybird_id__exact=""))

        return context


class SaveCode(LoginRequiredMixin, RedirectView):
    def dispatch(self, request, *args, **kwargs):
        if 'code' in kwargs and kwargs['code']:
            Settings.set('auth_code', unquote(kwargs['code']))
        elif 'code' in request.GET and request.GET['code']:
            Settings.set('auth_code', request.GET['code'])
        return super(SaveCode, self).dispatch(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return reverse('moneybird:index')


class ConceptOrderView(LoginRequiredMixin, DetailView):
    queryset = ConceptOrder.objects.all().prefetch_related('conceptorderdrink_set',
                                                           'conceptorderdrink_set__conceptorderdrinkline_set',
                                                           'conceptorderdrink_set__conceptorderdrinkline_set__product')

    @profile
    def dispatch(self, request, *args, **kwargs):
        return super(ConceptOrderView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ConceptOrderView, self).get_context_data(**kwargs)

        context['drink_create_form'] = ConceptOrderDrinkForm()

        for drink in context['object'].conceptorderdrink_set.all():
            drink.edit_form = ConceptOrderDrinkForm(instance=drink)
            drink.line_create_form = ConceptOrderDrinkLineForm()
            drink.line_create_form.html_id = "ConceptOrderDrinkLine-" + str(drink.pk)

            for line in drink.conceptorderdrinkline_set.all():
                line.edit_form = ConceptOrderDrinkLineForm(instance=line)

        return context


class ConceptOrderDrinkCreateView(LoginRequiredMixin, CreateView):
    model = ConceptOrderDrink
    form_class = ConceptOrderDrinkForm
    
    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(ConceptOrder, pk=self.kwargs['pk'])
        return super(ConceptOrderDrinkCreateView, self).dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        ctx = super(ConceptOrderDrinkCreateView, self).get_context_data(**kwargs)
        ctx['order'] = self.order
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.order = self.order
        self.object.save()
        return super(ConceptOrderDrinkCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('moneybird:order_view', kwargs={'pk': self.object.order.pk})


class ConceptOrderDrinkEditView(LoginRequiredMixin, UpdateView):
    model = ConceptOrderDrink
    form_class = ConceptOrderDrinkForm

    def get_context_data(self, **kwargs):
        ctx = super(ConceptOrderDrinkEditView, self).get_context_data(**kwargs)
        ctx['order'] = self.object.order
        return ctx

    def get_success_url(self):
        return reverse('moneybird:order_view', kwargs={'pk': self.object.order.pk})


class ConceptOrderDrinkDeleteView(LoginRequiredMixin, DeleteView):
    model = ConceptOrderDrink

    def get_success_url(self):
        return reverse('moneybird:order_view', kwargs={'pk': self.object.order.pk})


class ConceptOrderDrinkLineCreateView(LoginRequiredMixin, CreateView):
    model = ConceptOrderDrinkLine
    form_class = ConceptOrderDrinkLineForm

    def dispatch(self, request, *args, **kwargs):
        self.drink = get_object_or_404(ConceptOrderDrink, pk=self.kwargs['pk'])
        return super(ConceptOrderDrinkLineCreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(ConceptOrderDrinkLineCreateView, self).get_context_data(**kwargs)
        ctx['drink'] = self.drink
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.drink = self.drink
        self.object.save()
        return super(ConceptOrderDrinkLineCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('moneybird:order_view', kwargs={'pk': self.object.drink.order.pk})


class ConceptOrderDrinkLineEditView(LoginRequiredMixin, UpdateView):
    model = ConceptOrderDrinkLine
    form_class = ConceptOrderDrinkLineForm

    def get_context_data(self, **kwargs):
        ctx = super(ConceptOrderDrinkLineEditView, self).get_context_data(**kwargs)
        ctx['drink'] = self.object.drink
        return ctx

    def get_success_url(self):
        return reverse('moneybird:order_view', kwargs={'pk': self.object.drink.order.pk})


class ConceptOrderDrinkLineDeleteView(LoginRequiredMixin, DeleteView):
    model = ConceptOrderDrinkLine

    def get_success_url(self):
        return reverse('moneybird:order_view', kwargs={'pk': self.object.drink.order.pk})


class OrdersCreateFromFile(LoginRequiredMixin, FormView):
    form_class = FileForm
    template_name = 'moneybird/file_upload.html'
    success_url = reverse_lazy('moneybird:index')

    def _create_missing_objects(self, data):
        for customer in data['drinks'].keys():
            if not Customer.objects.filter(alexia_name=customer).exists():
                customer_obj = Customer()
                customer_obj.alexia_name = customer
                customer_obj.save()

        for product_id, product_name in data['products'].items():
            product, _ = Product.objects.get_or_create(alexia_id=product_id)
            product.alexia_name = product_name
            product.save()

    def form_valid(self, form):
        data = form.cleaned_json

        self._create_missing_objects(data)

        for customer_name, drinks in data['drinks'].items():
            order = ConceptOrder()
            order.customer = Customer.objects.get(alexia_name=customer_name)
            order.date = datetime.now()
            order.save()

            for drink in drinks:
                order_drink = ConceptOrderDrink()
                order_drink.order = order
                order_drink.date = datetime.strptime(drink['date'], '%d-%m-%Y')
                order_drink.name = drink['drink_name']

                for i, location in enumerate(drink['location']):
                    order_drink.locations += location
                    if i != len(drink['location']) - 1:
                        order_drink.locations += ", "

                order_drink.save()

                for product_id, quantity in drink['products'].items():
                    order_drink_line = ConceptOrderDrinkLine()
                    order_drink_line.drink = order_drink
                    order_drink_line.product = Product.objects.get(alexia_id=product_id)
                    order_drink_line.amount = quantity
                    order_drink_line.save()

        return super(OrdersCreateFromFile, self).form_valid(form)


class OrdersSendAllView(LoginRequiredMixin, View):
    def post(self, request):
        client_id = Settings.get("client_id")
        client_secret = Settings.get("client_secret")
        moneybird, do_redirect = Moneybird.instantiate_or_redirect(request, client_id, client_secret)
        if do_redirect: return do_redirect
        "https://moneybird.com/oauth/authorize?client_id=&redirect_uri=http://127.0.0.1:8000/moneybird/code&response_type=code&scope=sales_invoices"

        orders = ConceptOrder.objects.all()

        for order in orders:
            moneybird_order = order.as_moneybird()
            response = moneybird.create_invoice(moneybird.get_administrations()[0]['id'], moneybird_order)
            if response.status_code == 402:
                print("LIMIT REACHED")
                messages.error(request, "Failed to create invoice for {}. Invoice limit reached.".format(order.customer.alexia_name))
            elif response.status_code == 201:
                messages.success(request, "Invoice created successfully for {}.".format(order.customer.alexia_name))
                order.sent = True
                order.save()
            else:
                messages.error(request, "Failed to create invoice for {}: {}".format(order.customer.alexia_name, response.text))

        return redirect('moneybird:index')


class ConceptOrderDelete(LoginRequiredMixin, DeleteView):
    model = ConceptOrder
    success_url = reverse_lazy('moneybird:index')


class CustomerUpdate(LoginRequiredMixin, UpdateView):
    model = Customer
    success_url = reverse_lazy('moneybird:index')
    fields = '__all__'


class SettingsUpdate(LoginRequiredMixin, UpdateView):
    model = Settings
    success_url = reverse_lazy('moneybird:index')
    fields = '__all__'


class Products(LoginRequiredMixin, ListView):
    model = Product
    ordering = ['moneybird_id']

    def get_context_data(self, **kwargs):
        ctx = super(Products, self).get_context_data(**kwargs)

        ctx['create_form'] = ProductForm()

        for product in ctx['product_list']:
            product.edit_form = ProductForm(instance=product)

        return ctx


class ProductCreate(LoginRequiredMixin, CreateView):
    form_class = ProductForm
    template_name = 'moneybird/product_form.html'
    success_url = reverse_lazy('moneybird:products')


class ProductUpdate(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    success_url = reverse_lazy('moneybird:products')


class ProductDelete(LoginRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy('moneybird:products')