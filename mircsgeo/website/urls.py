from django.conf.urls import url
from django.conf import settings

from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^home$', views.home, name='home'),
    url(r'^upload_csv$', views.upload_csv, name='upload_csv'),
    url(r'^store_csv$', views.store_csv, name='store_csv'),
    url(r'^test_response$', views.test_response, name='test_response'),
    url(r'^create_table$', views.create_table, name='create_table')
]
