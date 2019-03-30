from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.views import View
from django.shortcuts import redirect, render, get_object_or_404, get_list_or_404
from django.conf import settings
from django.contrib import messages
from django.core import serializers
from .models import Corpus
from .forms import CorpusForm
import os
import csv
import numpy as np

def handle_uploaded_data(file_in, file_out, username, dataname):
    out = []
    inp = []
    with open(file_in, newline='') as csvfile:
        for l in list(csv.reader(csvfile)):
            inp.append([int(i) for i in l])
    with open(file_out, newline='') as csvfile:
        for l in list(csv.reader(csvfile)):
            out.append([int(i) for i in l])
    np.save( dataname +"_in.npy", inp)
    np.save( dataname +"_out.npy", out)

def delete_corpus_data(username, dataname):
    try:
        os.remove(os.path.join(settings.PATH_TO_USERS_FOLDER + username, settings.PATH_TO_CORPUS) + dataname + "_in.npy")
    except FileNotFoundError:
        return "Error during deletion : File could not be removed as it does not exist"
    try:
        os.remove(os.path.join(settings.PATH_TO_USERS_FOLDER + username, settings.PATH_TO_CORPUS) + dataname + "_out.npy")
    except FileNotFoundError:
        return "Error during deletion : File could not be removed as it does not exist"
    else:
        return "Corpus data successfully deleted"

def correct(file):
    with open(file, newline='') as csvfile:
        i = 0
        for l in list(csv.reader(csvfile)):
            if i==0:
                dim = len(l)
                i = 1
            if len(l) != dim:
                return False
            for j in l:
                try:
                    int(j) 
                except:
                    return False
    return True
    

def size(file):
    with open(file, newline='') as csvfile:
        i = len(list(csv.reader(csvfile)))
    return i

def dim(file):
    with open(file, newline='') as csvfile:
        d = len(list(csv.reader(csvfile))[0])
    return d

def create(request):
    if request.method == 'POST':
        form = CorpusForm(request.POST)
        if form.is_valid():
            new_corpus = form.save(commit=False)
            new_corpus.owner = request.user
            new_corpus.size = 0
            new_corpus.dim_in = 0
            new_corpus.dim_out = 0
            new_corpus.path = os.path.join(settings.PATH_TO_USERS_FOLDER + request.user.username, settings.PATH_TO_CORPUS) + new_corpus.name.replace(" ", "_")
            with open(new_corpus.path+"in.csv", 'wb+') as destination:
                for chunk in request.FILES['data_in'].chunks():
                    destination.write(chunk)
            with open(new_corpus.path+"out.csv", 'wb+') as destination:
                for chunk in request.FILES['data_out'].chunks():
                    destination.write(chunk)
            if (correct(new_corpus.path+"out.csv") and correct(new_corpus.path+"in.csv") and (size(new_corpus.path+"in.csv") == size(new_corpus.path+"out.csv"))):
                new_corpus.save()
                handle_uploaded_data(new_corpus.path+"out.csv", new_corpus.path+"in.csv", request.user.username, new_corpus.path+ "_" + str(new_corpus.pk))
            else:
                return HttpResponseBadRequest('Error: Form is not valid')
            new_corpus.size = size(new_corpus.path+"in.csv")
            new_corpus.dim_in = dim(new_corpus.path+"in.csv")
            new_corpus.dim_out = dim(new_corpus.path+"out.csv")
            new_corpus.path = new_corpus.path + "_" + str(new_corpus.pk)
            new_corpus.save()
            messages.info(request, 'Corpus successfully created!')
            return HttpResponseRedirect('/accounts/')
        else:
            forms=get_basic_forms(request)
            forms["corpus_form"]=form
            return render(request, 'ARNN/index.html', forms)

def edit(request, pk):
    corpus = get_object_or_404(Corpus, pk=pk)
    if request.method == 'POST':
        form = CorpusForm(request.POST, instance=corpus)
        if form.is_valid():
            new_corpus = form.save(commit=False)
            new_corpus.save()
            messages.info(request, 'Corpus successfully edited!')
            return HttpResponseRedirect('/accounts/')
        else:
            messages.error(request, 'Error: Form is not valid')
            return HttpResponseBadRequest('Error: Form is not valid')

def delete(request, pk):
    corpus = get_object_or_404(Corpus, pk=pk)
    delete_corpus_data(request.user.username, corpus.name.replace(" ", "_"))
    corpus.delete()
    messages.info(request, 'Corpus successfully deleted!')
    return HttpResponseRedirect('/accounts/')

def liste(request):
    corpus = Corpus.objects.filter(owner=request.user)
    corp_json = serializers.serialize('json', corpus)
    return HttpResponse(corp_json, content_type='json')