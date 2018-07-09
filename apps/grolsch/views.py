from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, FormView, DetailView

from apps.grolsch.forms import CreateProductFromUrlForm
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


class PriceChangeDetail(LoginRequiredMixin, DetailView):
    model = UnresolvedPriceChange
