from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect

import website.models
from .forms import UploadCsv

import pandas as pd


def home(request):
    context = {}
    return render(request, 'home.html', context)


def upload_csv(request):
    if request.method == 'POST':
        # Do some stuff
        form = UploadCsv(request.POST, request.FILES)
        if form.is_valid():
            request.session['data'] = pd.read_csv(request.FILES['csv_file'])
            return HttpResponseRedirect('/test_response')
    else:
        form = UploadCsv()
    return render(request, 'upload_csv.html', {'form': form})


def test_response(request):
    return HttpResponse('yay')


def Session():
    from aldjemy.core import get_engine
    engine = get_engine()
    _Session = sessionmaker(bind=engine)
    return _Session()
