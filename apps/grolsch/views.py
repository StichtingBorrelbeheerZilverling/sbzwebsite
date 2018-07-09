from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, FormView, DetailView, UpdateView

from apps.grolsch.forms import CreateProductFromUrlForm, PriceChangeResolveForm
from apps.grolsch.models import Product, UnresolvedPriceChange


class ProductList(LoginRequiredMixin, ListView):
    model = Product

    def get_context_data(self, **kwargs):
        context = super(ProductList, self).get_context_data(**kwargs)
        context['create_form'] = CreateProductFromUrlForm()
        return context


class ProductCreate(LoginRequiredMixin, FormView):
    form_class = CreateProductFromUrlForm
    template_name = "grolsch/product_create.html"
    success_url = reverse_lazy('grolsch:products')

    def form_valid(self, form):
        url = form.cleaned_data['url']
        track_price = form.cleaned_data['track_price']

        product = Product.create_from_url(url, track_price=track_price)
        product.save()
        return super(ProductCreate, self).form_valid(form)


class PriceChangeList(LoginRequiredMixin, ListView):
    model = UnresolvedPriceChange


class PriceChangeDetail(LoginRequiredMixin, DetailView):
    model = UnresolvedPriceChange

    def get_context_data(self, **kwargs):
        context = super(PriceChangeDetail, self).get_context_data(**kwargs)
        context['form'] = PriceChangeResolveForm()
        return context


class PriceChangeResolve(LoginRequiredMixin, FormView):
    form_class = PriceChangeResolveForm
    template_name = 'grolsch/unresolvedpricechange_detail.html'
    success_url = reverse_lazy('grolsch:price_changes')

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(UnresolvedPriceChange, pk=self.kwargs['pk'])
        return super(PriceChangeResolve, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PriceChangeResolve, self).get_context_data(**kwargs)
        context['object'] = self.object
        return context

    def form_valid(self, form):
        change_type = form.cleaned_data['price_change_type']

        if change_type == PriceChangeResolveForm.CHOICE_NEW_PRICE:
            self.object.product.last_price = self.object.new_price
            self.object.product.last_discount_price = None
            self.object.product.save()
            self.object.delete()
        elif change_type == PriceChangeResolveForm.CHOICE_DISCOUNT_PRICE:
            self.object.product.last_discount_price = self.object.new_price
            self.object.product.save()
            self.object.delete()
        else:
            raise Exception('Impossible')

        return super(PriceChangeResolve, self).form_valid(form)
