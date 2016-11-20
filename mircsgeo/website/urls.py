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
    url(r'^view/(?P<table>[^/]+)/$', views.view_dataset, name='view_dataset'),
    url(r'^manage/join/(?P<table>[^/]+)$', views.join_datasets, name='join_datasets'),
    url(r'^add_dataset_key/(?P<table>[^/]+)/$', views.add_dataset_key, name='add_dataset_key'),
    url(r'^get_dataset_keys/(?P<table>[^/]+)/$', views.get_dataset_keys, name='get_dataset_keys'),
    url(r'^manage/(?P<table>[^/]+)$', views.manage_dataset, name='manage_dataset'),
    url(r'^manage/append/(?P<table>[^/]+)$', views.append_dataset, name='append_dataset'),
    url(r'^manage/update/(?P<table>[^/]+)$', views.update_dataset, name='update_dataset'),
    url(r'^manage/append_column/(?P<table>[^/]+)$', views.append_column, name='append_column'),
    url(r'^get_dataset_page/(?P<table>[^/]+)/(?P<page_number>[0-9]+)/$', views.get_dataset_page, name='get_dataset_page'),
    url(r'^get_joined_dataset/(?P<table>[^/]+)/(?P<page_number>[0-9]+)/$', views.get_joined_dataset, name='get_joined_dataset'),
    url(r'^get_dataset_geojson/(?P<table>[^/]+)/(?P<page_number>[0-9]+)/$', views.get_dataset_geojson, name="get_dataset_geojson")
]
