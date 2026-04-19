from django.urls import re_path as url

from . import views

app_name = 'moneybird'

urlpatterns = [
    url(r'^$', view=views.Index.as_view(), name='index'),
    
    url(r'^code(/(?P<code>[0-9]+))?$', view=views.SaveAuthCode.as_view(), name='code'),

    # TODO: Make Customers editable via interface
    url(r'^customer/(?P<pk>[0-9]+)/edit$', view=views.CustomerUpdate.as_view(), name='customer_update'),

    url(r'^products$', view=views.Products.as_view(), name='products'),
    url(r'^product/add$', view=views.ProductCreate.as_view(), name='product_add'),
    url(r'^product/(?P<pk>[0-9]+)/edit$', view=views.ProductUpdate.as_view(), name='product_edit'),
    url(r'^product/(?P<pk>[0-9]+)/delete$', view=views.ProductDelete.as_view(), name='product_delete'),

    url(r'^product/types$', view=views.ProductTypes.as_view(), name='product_types'),
    url(r'^product/type/add$', view=views.ProductTypeCreate.as_view(), name='product_type_add'),
    url(r'^product/type/(?P<pk>[0-9]+)/edit$', view=views.ProductTypeUpdate.as_view(), name='product_type_edit'),
    url(r'^product/type/(?P<pk>[0-9]+)/delete$', view=views.ProductTypeDelete.as_view(), name='product_type_delete'),

    # TODO: create option to only send selected orders
    url(r'^order/(?P<pk>[0-9]+)$', view=views.ConceptOrderView.as_view(), name='order_view'),
    url(r'^order/(?P<pk>[0-9]+)/delete$', view=views.ConceptOrderDelete.as_view(), name='order_delete'),
    url(r'^order/createFromFile$', view=views.OrdersCreateFromFile.as_view(), name='orders_create_from_file'),
    url(r'^order/create$', view=views.OrdersCreate.as_view(), name='orders_create'),
    url(r'^order/sendAll$', view=views.OrdersSendAllView.as_view(), name='orders_send_all'),
    url(r'^order/sendSelected$', view=views.OrdersSendSelectedView.as_view(), name='orders_send_selected'),

    url(r'^order/(?P<pk>[0-9]+)/drink/create$', view=views.ConceptOrderDrinkCreateView.as_view(), name='order_drink_create'),
    url(r'^order/drink/(?P<pk>[0-9]+)/edit$', view=views.ConceptOrderDrinkEditView.as_view(), name='order_drink_edit'),
    url(r'^order/drink/(?P<pk>[0-9]+)/delete$', view=views.ConceptOrderDrinkDeleteView.as_view(), name='order_drink_delete'),

    url(r'^order/drink/(?P<pk>[0-9]+)/line/create', view=views.ConceptOrderDrinkLineCreateView.as_view(), name='order_drink_line_create'),
    url(r'^order/drink/line/(?P<pk>[0-9]+)/edit', view=views.ConceptOrderDrinkLineEditView.as_view(), name='order_drink_line_edit'),
    url(r'^order/drink/line/(?P<pk>[0-9]+)/delete', view=views.ConceptOrderDrinkLineDeleteView.as_view(), name='order_drink_line_delete'),
]
