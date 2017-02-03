from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', view=views.Index.as_view(), name='index'),
    url(r'^db/(?P<name>.+)$', view=views.SelectDB.as_view(), name='select_db'),
    url(r'^code(/(?P<code>.+))?$', view=views.SaveCode.as_view(), name='code'),
    url(r'^clear_cache/$', view=views.ClearCache.as_view(), name='clear_cache'),
    url(r'^send/$', view=views.SendToMultivers.as_view(), name='send'),
    url(r'^upload/$', view=views.UploadJsonData.as_view(), name='upload'),
    url(r'^costumer/(?P<pk>.+)/edit$', view=views.CostumerUpdate.as_view(), name='costumer_update'),
    url(r'^product/(?P<pk>.+)/edit$', view=views.ProductUpdate.as_view(), name='product_update'),
    url(r'^location/(?P<pk>.+)/edit$', view=views.LocationUpdate.as_view(), name='location_update'),
    url(r'^settings/(?P<pk>.+)/edit$', view=views.SettingsUpdate.as_view(), name='setting_update'),
]