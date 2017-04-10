import json
import re
from urllib.parse import unquote

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.views.generic import UpdateView
from django.views.generic.base import RedirectView, View

from apps.multivers.defaults import make_orderline, make_order
from apps.multivers.forms import FileForm
from . import tools
from .models import Settings, Costumer, Product, Location

DISCOUNT = 'discount'

data_cache = {}


class Index(LoginRequiredMixin, View):
    def get(self, request):
        result = tools.oauth(request)
        if result:
            return result
        else:
            if not Settings.objects.filter(key=DISCOUNT).exists():
                new_setting = Settings()
                new_setting.key = DISCOUNT
                new_setting.save()
                return redirect(new_setting)
            if Settings.objects.filter(key=DISCOUNT, value__isnull=True).exists() or not re.match(r'\d+(\.\d+)?', Settings.objects.get(key=DISCOUNT).value):
                return redirect(Settings.objects.get(key=DISCOUNT))
            if Settings.objects.filter(key='db').exists():
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

                    costumers = Costumer.objects.filter(alexia_name__in=cache['drinks'].keys())
                    if costumers.count() >= len(cache['drinks']):
                        return render(request, 'multivers/index.html', {'discount': Settings.objects.get(key=DISCOUNT)})
                    else:
                        for x in cache['drinks'].keys():
                            if not Costumer.objects.filter(alexia_name=x).exists():
                                new_costumer = Costumer()
                                new_costumer.alexia_name = x
                                new_costumer.save()
                                return redirect(new_costumer)
                        raise Exception('State impossible')
                else:
                    return redirect(reverse('multivers:upload'))
            else:
                return render(request, 'multivers/db.html', {'dbs': tools.get_administrations()})


class SendToMultivers(LoginRequiredMixin, View):
    def get(self, request):
        result = tools.oauth(request)
        if result:
            return result
        else:
            result = []
            for costumer_name, drinks in data_cache[request.user]['drinks'].items():
                order_lines = []
                for drink in drinks:
                    locations = Location.objects.filter(name__in=drink['location'])
                    discount = locations.filter(no_discount=Location.ALWAYS_DISCOUNT).exists() or not locations.filter(no_discount=Location.NO_DISCOUNT).exists()

                    order_lines.extend(
                        make_orderline(product_id, amount, drink['drink_name'], drink['date'], discount)
                        for product_id, amount in drink['products'].items()
                    )
                order = make_order(costumer_name, order_lines)
                sr, response = tools.send_to_multivers(order)
                if not sr:
                    return HttpResponse('Error {} {}<br>\n<br>\n{}'.format(response.status_code, response.content, json.dumps(order)))
                else:
                    json_response = json.loads(response.content.decode('UTF-8'))
                    result.append((costumer_name, json_response['orderId'], json_response['totalOrderAmount']))
            return render(request, 'multivers/send.html', {'result': result})


class SaveCode(LoginRequiredMixin, RedirectView):
    def dispatch(self, request, *args, **kwargs):
        if 'code' in kwargs and kwargs['code']:
            tools.save_setting(key='auth_code', value=unquote(kwargs['code']))
        elif 'code' in request.GET and request.GET['code']:
            tools.save_setting(key='auth_code', value=unquote(request.GET['code']))
        return super(SaveCode, self).dispatch(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return reverse('multivers:index')


class SelectDB(LoginRequiredMixin, RedirectView):
    def dispatch(self, request, *args, **kwargs):
        tools.save_setting('db', kwargs['name'])
        return super(SelectDB, self).dispatch(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return reverse('multivers:index')


class ClearCache(LoginRequiredMixin, RedirectView):
    def dispatch(self, request, *args, **kwargs):
        try:
            del data_cache[request.user]
        except NameError:
            pass
        except KeyError:
            pass
        return super(ClearCache, self).dispatch(request, *args, **kwargs)

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
    model = Costumer
    success_url = reverse_lazy('multivers:index')
    fields = '__all__'


class ProductUpdate(LoginRequiredMixin, UpdateView):
    model = Product
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
