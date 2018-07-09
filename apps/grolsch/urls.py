from django.conf.urls import url
from . import views

urlpatterns = [
    url('^products$', views.ProductList.as_view(), name='products'),
    url('^product/create$', views.ProductCreate.as_view(), name='product_create'),

    url('^price_change/(?P<pk>[0-9]+)$', views.PriceChangeDetail.as_view(), name='price_change_detail'),
]
