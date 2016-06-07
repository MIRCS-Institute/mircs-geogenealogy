from django.conf.urls import url
from django.conf import settings

from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^home$', views.home, name='home'),
    url(r'^upload_csv$', views.upload_csv, name='upload_csv'),
    url(r'^test_response$', views.test_response, name='test_response')
]
