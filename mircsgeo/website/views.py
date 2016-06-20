from django.shortcuts import render, redirect
from django.template import RequestContext
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.conf import settings
from sqlalchemy.orm import sessionmaker

import website.models as m
from .forms import Uploadfile

import pandas as pd

import os
import uuid

import datetime

schema = "mircs"


def home(request):
    db = Session().connection()
    session = m.get_session()
    tables = session.query(
        m.DATASETS.original_filename,
        m.DATASETS.table_name,
        m.DATASETS.upload_date
    ).all()
    session.close()

    print tables[0].original_filename
    context = {'tables': tables}
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
        df = pd.read_csv(absolute_path)
        table_name = str(uuid.uuid4()).replace("-", "")

        # Get an sqlalchemy session automap'ed to the database
        session = m.get_session()
        # Create a new dataset to be added
        dataset = m.DATASETS(
            original_filename=request.session['real_filename'],
            table_name=table_name,
            upload_date=datetime.datetime.now(),
        )
        # Add the dataset to the session and commit the session to the database
        session.add(dataset)
        session.commit()

        df.columns = [x.replace(" ", "_") for x in df.columns]

        df.to_sql(table_name, Session().connection(), schema=schema, index=True, index_label="id")
        session.close()
        return redirect('/')
    else:
        return None


def view_dataset(request, table):
    # Get a session
    session = m.get_session()
    # Get the name of the file used to create the table being queried
    file_name = str(session.query(m.DATASETS.original_filename).filter(m.DATASETS.table_name == table).one()[0])
    session.close

    db = Session().connection()
    df = pd.read_sql("SELECT * FROM "+schema+"."+table+" LIMIT 100", db, params={'schema':schema, 'table':table})
    columns = df.columns.tolist()
    rows = df.values.tolist()
    return render(request, 'view_dataset.html', {'dataset': rows, 'columns': columns, 'tablename':file_name})


def test_response(request):
    return HttpResponse('yay')


def Session():
    from aldjemy.core import get_engine
    engine = get_engine()
    _Session = sessionmaker(bind=engine)
    return _Session()
