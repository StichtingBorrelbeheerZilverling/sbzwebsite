import json
from datetime import datetime
from urllib.parse import unquote

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, DeleteView, CreateView
from django.views.generic import UpdateView
from django.views.generic.base import RedirectView, View
from django.views.generic.detail import DetailView

from apps.multivers.defaults import make_orderline, make_order
from apps.multivers.forms import FileForm, ProductForm, ConceptOrderDrinkForm, ConceptOrderDrinkLineForm, SendOrdersForm
from apps.multivers.tools import Multivers, MultiversOrderLine, MultiversOrder
from apps.util.profiling import profile
from . import tools
from .models import Settings, Customer, Product, Location, ConceptOrder, ConceptOrderDrink, ConceptOrderDrinkLine


class Index(LoginRequiredMixin, ListView):
    queryset = ConceptOrder.objects.all().prefetch_related('conceptorderdrink_set')

    def get_context_data(self, **kwargs):
        context = super(Index, self).get_context_data(**kwargs)

        context['send_form'] = SendOrdersForm()
        context['create_order_form'] = FileForm()

        context['new_products'] = Product.objects.filter(Q(multivers_id__isnull=True) | Q(multivers_id__exact=""))
        context['new_customers'] = Customer.objects.filter(Q(multivers_id__isnull=True) | Q(multivers_id__exact=""))
        context['new_locations'] = Location.objects.filter(no_discount__isnull=True)

        return context


class SaveCode(LoginRequiredMixin, RedirectView):
    def dispatch(self, request, *args, **kwargs):
        if 'code' in kwargs and kwargs['code']:
            Settings.set('auth_code', unquote(kwargs['code']))
        elif 'code' in request.GET and request.GET['code']:
            Settings.set('auth_code', request.GET['code'])
        return super(SaveCode, self).dispatch(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return reverse('multivers:index')


class ConceptOrderView(LoginRequiredMixin, DetailView):
    queryset = ConceptOrder.objects.all().prefetch_related('conceptorderdrink_set',
                                                           'conceptorderdrink_set__locations',
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
        return reverse('multivers:order_view', kwargs={'pk': self.object.order.pk})


class ConceptOrderDrinkEditView(LoginRequiredMixin, UpdateView):
    model = ConceptOrderDrink
    form_class = ConceptOrderDrinkForm

    def get_context_data(self, **kwargs):
        ctx = super(ConceptOrderDrinkEditView, self).get_context_data(**kwargs)
        ctx['order'] = self.object.order
        return ctx

    def get_success_url(self):
        return reverse('multivers:order_view', kwargs={'pk': self.object.order.pk})


class ConceptOrderDrinkDeleteView(LoginRequiredMixin, DeleteView):
    model = ConceptOrderDrink

    def get_success_url(self):
        return reverse('multivers:order_view', kwargs={'pk': self.object.order.pk})


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
        return reverse('multivers:order_view', kwargs={'pk': self.object.drink.order.pk})


class ConceptOrderDrinkLineEditView(LoginRequiredMixin, UpdateView):
    model = ConceptOrderDrinkLine
    form_class = ConceptOrderDrinkLineForm

    def get_context_data(self, **kwargs):
        ctx = super(ConceptOrderDrinkLineEditView, self).get_context_data(**kwargs)
        ctx['drink'] = self.object.drink
        return ctx

    def get_success_url(self):
        return reverse('multivers:order_view', kwargs={'pk': self.object.drink.order.pk})


class ConceptOrderDrinkLineDeleteView(LoginRequiredMixin, DeleteView):
    model = ConceptOrderDrinkLine

    def get_success_url(self):
        return reverse('multivers:order_view', kwargs={'pk': self.object.drink.order.pk})


class OrdersCreateFromFile(LoginRequiredMixin, FormView):
    form_class = FileForm
    template_name = 'multivers/file_upload.html'
    success_url = reverse_lazy('multivers:index')

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

        alexia_locations = set()

        for drinks in data['drinks'].values():
            for drink in drinks:
                for location in drink['location']:
                    alexia_locations.add(location)

        for alexia_location in alexia_locations:
            if not Location.objects.filter(name=alexia_location).exists():
                location = Location()
                location.name = alexia_location
                location.save()

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
                order_drink.save()

                for location in drink['location']:
                    order_drink.locations.add(Location.objects.get(name=location))

                for product_id, quantity in drink['products'].items():
                    order_drink_line = ConceptOrderDrinkLine()
                    order_drink_line.drink = order_drink
                    order_drink_line.product = Product.objects.get(alexia_id=product_id)
                    order_drink_line.amount = quantity
                    order_drink_line.save()

        return super(OrdersCreateFromFile, self).form_valid(form)


class OrdersSendAllView(LoginRequiredMixin, FormView):
    form_class = SendOrdersForm

    def form_valid(self, form):
        multivers, do_redirect = Multivers.instantiate_or_redirect(self.request)
        if do_redirect: return do_redirect

        admin = Settings.get('db')

        orders = ConceptOrder.objects.all()

        for order in orders:
            multivers_order = order.as_multivers(revenue_account=form.cleaned_data['override_revenue_account'])
            multivers.create_order(administration=admin, order=multivers_order)

        return redirect('multivers:index')


class ConceptOrderDelete(LoginRequiredMixin, DeleteView):
    model = ConceptOrder
    success_url = reverse_lazy('multivers:index')


class CustomerUpdate(LoginRequiredMixin, UpdateView):
    model = Customer
    success_url = reverse_lazy('multivers:index')
    fields = '__all__'


class LocationUpdate(LoginRequiredMixin, UpdateView):
    model = Location
    success_url = reverse_lazy('multivers:index')
    fields = '__all__'


class SettingsUpdate(LoginRequiredMixin, UpdateView):
    model = Settings
    success_url = reverse_lazy('multivers:index')
    fields = '__all__'


class Products(LoginRequiredMixin, ListView):
    model = Product
    ordering = ['multivers_id']

    def get_context_data(self, **kwargs):
        ctx = super(Products, self).get_context_data(**kwargs)

        ctx['create_form'] = ProductForm()

        for product in ctx['product_list']:
            product.edit_form = ProductForm(instance=product)

        return ctx


class ProductCreate(LoginRequiredMixin, CreateView):
    form_class = ProductForm
    template_name = 'multivers/product_form.html'
    success_url = reverse_lazy('multivers:products')


class ProductUpdate(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    success_url = reverse_lazy('multivers:products')


class ProductDelete(LoginRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy('multivers:products')


def test(request):
    multivers = Multivers(request)

    line = MultiversOrderLine(date=datetime.now(),
                              description="DiMiBo - Grolsch Premiumbier",
                              discount=0.05,
                              product_id="2001",
                              quantity=105.0)

    order = MultiversOrder(date=datetime.now(),
                           reference="Borrels Juni",
                           payment_condition_id="14",
                           customer_id="2008001",
                           customer_vat_type="1",
                           processor_id=38,
                           processor_name="Pieter Bos")

    order.add_line(line)
    order.add_line(line)

    response = multivers.create_order("MVL48759", order)

    return HttpResponse(json.dumps(response), content_type="application/json")
