from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', view=views.index, name='index'),
    url(r'^construction/', view=views.construction, name='construction'),
    url(r'^contact/', view=views.contact, name='contact'),
]
