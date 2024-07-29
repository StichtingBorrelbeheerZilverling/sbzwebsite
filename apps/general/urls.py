from django.urls import re_path as url

from . import views

app_name = 'general'

urlpatterns = [
    url(r'^$', view=views.index, name='index'),
    url(r'^construction/', view=views.construction, name='construction'),
    url(r'^contact/', view=views.contact, name='contact'),

    url(r'^login$', view=views.login, name='login'),
    url(r'^logout$', view=views.logout, name='logout'),
]
