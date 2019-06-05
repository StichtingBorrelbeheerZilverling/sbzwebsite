from django.conf.urls import url

from apps.flowguard import views

urlpatterns = [
    url(r'api/1/update', views.update, name='update'),
    url(r'monitor/', views.monitor, name='monitor'),
]
