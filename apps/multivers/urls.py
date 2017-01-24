from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', view=views.index, name='index'),
    url(r'^db/(?P<name>.+)', view=views.select_db),
    url(r'^code(/(?P<code>.+))?$', view=views.save_code, name='code'),
    url(r'^reset/$', view=views.reset, name='reset'),
]