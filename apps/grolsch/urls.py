from django.urls import re_path as url
from . import views

app_name = 'grolsch'

urlpatterns = [
    url('^products$', views.ProductList.as_view(), name='products'),
    url('^product/create$', views.ProductCreate.as_view(), name='product_create'),
    url('^product/(?P<pk>[0-9]+)/delete$', views.ProductDelete.as_view(), name='product_delete'),

    url('^price_changes$', views.PriceChangeList.as_view(), name='price_changes'),
    url('^price_change/(?P<pk>[0-9]+)$', views.PriceChangeDetail.as_view(), name='price_change_detail'),
    url('^price_change/(?P<pk>[0-9]+)/resolve$', views.PriceChangeResolve.as_view(), name='price_change_resolve')
]
