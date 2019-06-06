from django.conf.urls import url

from apps.flowguard import views

urlpatterns = [
    url(r'api/1/update$', views.update, name='update'),
    url(r'monitor/$', views.monitor, name='monitor'),
    url(r'stats/$', views.stats, name='stats'),
    url(r'lookup/$', views.lookup, name='lookup'),
    url(r'history/$', views.history, name='history'),
    url(r'history/(?P<year>[0-9]+)/(?P<month>[0-9]+)$', views.history, name='history_month'),
]
