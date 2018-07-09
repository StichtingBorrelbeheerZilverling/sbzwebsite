from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', view=views.Index.as_view(), name='index'),
    url(r'^code(/(?P<code>[0-9]+))?$', view=views.SaveCode.as_view(), name='code'),

    url(r'^customer/(?P<pk>[0-9]+)/edit$', view=views.CustomerUpdate.as_view(), name='customer_update'),
    url(r'^location/(?P<pk>[0-9]+)/edit$', view=views.LocationUpdate.as_view(), name='location_update'),
    url(r'^settings/(?P<pk>[0-9]+)/edit$', view=views.SettingsUpdate.as_view(), name='settings_update'),

    url(r'^products', view=views.Products.as_view(), name='products'),
    url(r'^product/(?P<pk>[0-9]+)/edit$', view=views.ProductUpdate.as_view(), name='product_edit'),
    url(r'^product/(?P<pk>[0-9]+)/delete$', view=views.ProductDelete.as_view(), name='product_delete'),

    url(r'^order/(?P<pk>[0-9]+)$', view=views.ConceptOrderView.as_view(), name='order_view'),
    url(r'^order/(?P<pk>[0-9]+)/delete$', view=views.ConceptOrderDelete.as_view(), name='order_delete'),
    url(r'^order/createFromFile$', view=views.OrdersCreateFromFile.as_view(), name='orders_create_from_file'),
    url(r'^order/sendAll$', view=views.OrdersSendAllView.as_view(), name='orders_send_all'),

    url(r'^order/(?P<pk>[0-9]+)/drink/create$', view=views.ConceptOrderDrinkCreateView.as_view(), name='order_drink_create'),
    url(r'^order/drink/(?P<pk>[0-9]+)/edit$', view=views.ConceptOrderDrinkEditView.as_view(), name='order_drink_edit'),
    url(r'^order/drink/(?P<pk>[0-9]+)/delete$', view=views.ConceptOrderDrinkDeleteView.as_view(), name='order_drink_delete'),

    url(r'^order/drink/(?P<pk>[0-9]+)/line/create', view=views.ConceptOrderDrinkLineCreateView.as_view(), name='order_drink_line_create'),
    url(r'^order/drink/line/(?P<pk>[0-9]+)/edit', view=views.ConceptOrderDrinkLineEditView.as_view(), name='order_drink_line_edit'),
    url(r'^order/drink/line/(?P<pk>[0-9]+)/delete', view=views.ConceptOrderDrinkLineDeleteView.as_view(), name='order_drink_line_delete'),

    url(r'^test$', view=views.test, name='test'),
]
