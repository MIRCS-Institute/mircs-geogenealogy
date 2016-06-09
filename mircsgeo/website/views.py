from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.conf import settings

import website.models
from .forms import UploadCsv

import pandas as pd

import os
import uuid


def home(request):
    context = {}
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


def test_response(request):
    return HttpResponse('yay')


def Session():
    from aldjemy.core import get_engine
    engine = get_engine()
    _Session = sessionmaker(bind=engine)
    return _Session()
