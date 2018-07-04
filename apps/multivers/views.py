import json

from datetime import datetime
import re
from urllib.parse import unquote

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, DeleteView
from django.views.generic import UpdateView
from django.views.generic.base import RedirectView, View

from apps.multivers.defaults import make_orderline, make_order
from apps.multivers.forms import FileForm, ProductForm
from apps.multivers.tools import Multivers, MultiversOrderLine, MultiversOrder
from . import tools
from .models import Settings, Customer, Product, Location

DISCOUNT = 'discount'

data_cache = {}



# Settings to check: DISCOUNT, db,

class Index(LoginRequiredMixin, View):
    def get(self, request):
        multivers, redirect = Multivers.instantiate_or_redirect(request)

        if redirect:
            return redirect

        if request.user in data_cache:
            cache = data_cache[request.user]
            for alexia_id, alexia_name in cache['products'].items():
                product = Product.objects.filter(alexia_id=alexia_id)
                if product.exists():
                    first = product.first()
                    if first.alexia_name != alexia_name:
                        first.alexia_name = alexia_name
                        first.save()
                else:
                    new_product = Product()
                    new_product.alexia_id = alexia_id
                    new_product.alexia_name = alexia_name
                    new_product.save()
                    return redirect(new_product)

            location = set(l for x in [d['location'] for a in cache['drinks'].values() for d in a] for l in x)
            db_location = [x[0] for x in Location.objects.all().values_list('name')]
            for l in location:
                if l not in db_location:
                    new_location = Location()
                    new_location.name = l
                    new_location.save()
                    return redirect(new_location)

            customers = Customer.objects.filter(alexia_name__in=cache['drinks'].keys())
            if customers.count() >= len(cache['drinks']):
                return render(request, 'multivers/index.html', {'discount': Settings.objects.get(key=DISCOUNT)})
            else:
                for x in cache['drinks'].keys():
                    if not Customer.objects.filter(alexia_name=x).exists():
                        new_customer = Customer()
                        new_customer.alexia_name = x
                        new_customer.save()
                        return redirect(new_customer)
                raise Exception('State impossible')
        else:
            return redirect(reverse('multivers:upload'))


class SendToMultivers(LoginRequiredMixin, View):
    def get(self, request):
        result = tools.oauth(request)
        if result:
            return result
        else:
            result = []
            for customer_name, drinks in data_cache[request.user]['drinks'].items():
                order_lines = []
                for drink in drinks:
                    locations = Location.objects.filter(name__in=drink['location'])
                    discount = locations.filter(no_discount=Location.ALWAYS_DISCOUNT).exists() or not locations.filter(no_discount=Location.NO_DISCOUNT).exists()

                    order_lines.extend(
                        make_orderline(product_id, amount, drink['drink_name'], drink['date'], discount)
                        for product_id, amount in drink['products'].items()
                    )
                order = make_order(customer_name, order_lines)
                sr, response = tools.send_to_multivers(order)
                if not sr:
                    return HttpResponse('Error {} {}<br>\n<br>\n{}'.format(response.status_code, response.content, json.dumps(order)))
                else:
                    json_response = json.loads(response.content.decode('UTF-8'))
                    result.append((customer_name, json_response['orderId'], json_response['totalOrderAmount']))
            return render(request, 'multivers/send.html', {'result': result})


class SaveCode(LoginRequiredMixin, RedirectView):
    def dispatch(self, request, *args, **kwargs):
        if 'code' in kwargs and kwargs['code']:
            Settings.set('auth_code', unquote(kwargs['code']))
        elif 'code' in request.GET and request.GET['code']:
            Settings.set('auth_code', request.GET['code'])
        return super(SaveCode, self).dispatch(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return reverse('multivers:index')


class SelectDB(LoginRequiredMixin, RedirectView):
    def dispatch(self, request, *args, **kwargs):
        tools.save_setting('db', kwargs['name'])
        return super(SelectDB, self).dispatch(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return reverse('multivers:index')


class UploadJsonData(LoginRequiredMixin, FormView):
    form_class = FileForm
    template_name = 'multivers/file_upload.html'
    success_url = reverse_lazy('multivers:index')

    def form_valid(self, form):
        data_cache[self.request.user] = form.cleaned_json
        return super(UploadJsonData, self).form_valid(form)


class CostumerUpdate(LoginRequiredMixin, UpdateView):
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

        for product in ctx['product_list']:
            product.edit_form = ProductForm(instance=product)

        return ctx


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
