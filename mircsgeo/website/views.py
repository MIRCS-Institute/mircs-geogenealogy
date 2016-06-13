from django.shortcuts import render, redirect
from django.template import RequestContext
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.conf import settings
from sqlalchemy.orm import sessionmaker

import website.models
from .forms import UploadCsv

import pandas as pd

import os
import uuid

schema = "mircs"

def home(request):
    db = Session().connection()
    tables = pd.read_sql("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = %(schema)s AND tablename != 'spatial_ref_sys'",db, params={'schema':schema})
    print tables
    context = {'tables': tables.tablename.tolist() }
    return render(request, 'home.html', context)


def upload_csv(request):
    if request.method == 'POST':
        return HttpResponseRedirect('test_response')
    else:
        form = UploadCsv()
    return render(request, 'upload_csv.html', {'form': form})


def store_csv(request):
    if request.method == 'POST':
        # Do some stuff
        form = UploadCsv(request.POST, request.FILES)
        print "got a post"
        print request.POST
        print request.FILES['csv_file']
        if form.is_valid():
            request.session['real_filename'] = request.FILES['csv_file'].name
            request.session['temp_filename'] = str(uuid.uuid4())
            request.session['filetype'] = 'csv'

            absolute_path = os.path.join(os.path.dirname(__file__), settings.MEDIA_ROOT, request.session['temp_filename'])
            df = pd.read_csv(request.FILES['csv_file'])
            df.to_csv(absolute_path, index=False)
            columns = df.columns.tolist()
            rows = df[0:10].values.tolist()
            for row in rows:
                for i, e in enumerate(row):
                    if pd.isnull(e):
                        row[i] = 'null'
            print rows
            print JsonResponse({'columns': columns, 'rows': rows})
            return JsonResponse({'columns': columns, 'rows': rows})
    else:
        return None

def create_table(request):
    if request.method == 'POST':
        # Do some stuff
        post_data = dict(request.POST)
        primary_key =  post_data['p_key']
        primary_key = [x.replace(" ", "_") for x in primary_key]
        absolute_path = os.path.join(os.path.dirname(__file__), settings.MEDIA_ROOT, request.session['temp_filename'])
        df = pd.read_csv(absolute_path)
        df.columns = [x.replace(" ", "_") for x in df.columns]
        db = Session().connection()
        df.to_sql(request.session['real_filename'].replace(".csv","").lower(), db, schema=schema)
        return redirect('/')
    else:
        return None

def view_dataset(request, table):
    db = Session().connection()
    df = pd.read_sql("SELECT * FROM "+schema+"."+table+" LIMIT 100", db, params={'schema':schema, 'table':table})
    columns = df.columns.tolist()
    rows = df.values.tolist()
    return render(request, 'view_dataset.html', {'dataset': rows, 'columns': columns, 'tablename':table})


def test_response(request):
    return HttpResponse('yay')


def Session():
    from aldjemy.core import get_engine
    engine = get_engine()
    _Session = sessionmaker(bind=engine)
    return _Session()
