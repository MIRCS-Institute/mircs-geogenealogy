from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

import website.models

import pandas as pd


def home(request):
    context = {}
    return render(request, 'home.html', context)


def Session():
    from aldjemy.core import get_engine
    engine = get_engine()
    _Session = sessionmaker(bind=engine)
    return _Session()
