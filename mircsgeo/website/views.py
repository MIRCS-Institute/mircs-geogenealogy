from django.shortcuts import render, redirect
from django.template import RequestContext
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.conf import settings
from sqlalchemy.orm import sessionmaker

import website.models
from .forms import Uploadfile

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


def upload_file(request):
    if request.method == 'POST':
        return HttpResponseRedirect('test_response')
    else:
        form = Uploadfile()
    return render(request, 'upload_file.html', {'form': form})


def store_file(request):
    if request.method == 'POST':
        # Do some stuff
        form = Uploadfile(request.POST, request.FILES)
        if form.is_valid():
            request.session['real_filename'] = request.FILES['file_upload'].name
            request.session['temp_filename'] = str(uuid.uuid4())
            request.session['filetype'] = os.path.splitext(request.session['real_filename'])[1]

            absolute_path = os.path.join(os.path.dirname(__file__), settings.MEDIA_ROOT, request.session['temp_filename'])
            if request.session['filetype'].lower() == '.csv':
                df = pd.read_csv(request.FILES['file_upload'])
            elif request.session['filetype'].lower() == '.xlsx':
                df = pd.read_excel(request.FILES['file_upload'])
            else:
                # TODO: Add a proper error handler for invalid file uploads. Probably inform the user somehow
                raise Exception("invalid file type uploaded: %s" % request.session['filetype'])
            df.to_csv(absolute_path, index=False)
            columns = df.columns.tolist()
            rows = df[0:10].values.tolist()
            for row in rows:
                for i, e in enumerate(row):
                    if pd.isnull(e):
                        row[i] = 'null'
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
        df = pd.read_file(absolute_path)
        df.columns = [x.replace(" ", "_") for x in df.columns]
        db = Session().connection()
        df.to_sql(request.session['real_filename'].replace(".file","").lower(), db, schema=schema)
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
