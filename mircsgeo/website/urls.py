from django.conf.urls import url
from django.conf import settings

from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^home$', views.home, name='home'),
    url(r'^upload_file$', views.upload_file, name='upload_file'),
    url(r'^store_file$', views.store_file, name='store_file'),
    url(r'^test_response$', views.test_response, name='test_response'),
    url(r'^create_table$', views.create_table, name='create_table'),
    url(r'^view/(?P<table>[^/]+)/$', views.view_dataset, name='view_dataset')
]
