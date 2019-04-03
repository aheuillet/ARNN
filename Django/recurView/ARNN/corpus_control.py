from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.views import View
from django.shortcuts import redirect, render, get_object_or_404, get_list_or_404
from django.conf import settings
from django.contrib import messages
from django.core import serializers
from .models import Corpus
from .forms import CorpusForm, CorpusGenerateForm
from .generate import write_csv, generate_shape_tracking_array, generate_shape
import os
import csv
import numpy as np
import zipfile
import io


def handle_uploaded_data(file_in, file_out, username, dataname):
    """ This function generates npy files from the uploaded corpus csv files

        Inputs:
        -file_in: A string containing the path to the input file
        -file_out: A string containing the path to the output file
        -username: A string containing the username of the corpus' owner
        -dataname: A string containing the path where to store the generated NPY files.
    """
    out = []
    inp = []
    with open(file_in, newline='') as csvfile:
        for l in list(csv.reader(csvfile)):
            inp.append([int(i) for i in l])
    with open(file_out, newline='') as csvfile:
        for l in list(csv.reader(csvfile)):
            out.append([int(i) for i in l])
    np.save(dataname + "_in.npy", inp)
    np.save(dataname + "_out.npy", out)


def delete_corpus_data(username, dataname):
    """ This function removes the files associated with a corpus.

        Inputs:
        -username: A string containing the username of the corpus' owner.
        -dataname: A string containing the name of the corpus.
    """
    try:
        os.remove(os.path.join(settings.PATH_TO_USERS_FOLDER +
                               username, settings.PATH_TO_CORPUS) + dataname + "_in.npy")
    except FileNotFoundError:
        return "Error during deletion : File could not be removed as it does not exist"
    try:
        os.remove(os.path.join(settings.PATH_TO_USERS_FOLDER +
                               username, settings.PATH_TO_CORPUS) + dataname + "_out.npy")
    except FileNotFoundError:
        return "Error during deletion : File could not be removed as it does not exist"
    else:
        return "Corpus data successfully deleted"


def correct(file):
    """ This function checks if the corpus contains only integers or floats and if its
    dimension is correct.

        Inputs:
        -file: The file to parse.
    """
    with open(file, newline='') as csvfile:
        i = 0
        for l in list(csv.reader(csvfile)):
            if i == 0:
                dim = len(l)
                i = 1
            if len(l) != dim:
                return False
            for j in l:
                try:
                    float(j)
                except:
                    return False
    return True

def generate(request):
    """ This function generates a new corpus after receiving a request from the client.

        Inputs:
        -request: The HTTP request from the client.
    """
    if request.method == 'POST':
        form = CorpusGenerateForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            size = form.cleaned_data['size']
            dim = form.cleaned_data['dim']
            min_val = form.cleaned_data['min_val']
            max_val = form.cleaned_data['max_val']
            seed = form.cleaned_data['seed']
            corpus_path = os.path.join(os.path.join(settings.PATH_TO_USERS_FOLDER, os.path.join(request.user.username, settings.PATH_TO_CORPUS)), name.replace(" ", "_"))
            generate_shape(corpus_path+"_in.csv", corpus_path+"_out.csv", size, dim, min_val, max_val, seed)
            corpus = Corpus.objects.create(name=name, size=size, dim_in=dim, dim_out=dim, path=corpus_path, owner=request.user)
            corpus.save()
            handle_uploaded_data(corpus_path+"_in.csv", corpus_path+"_out.csv", request.user.username, corpus_path)
            messages.success(request, 'Corpus successfully generated!')
            return HttpResponseRedirect('/accounts/')
        else:
            return HttpResponseBadRequest("Error: Form is not valid")
    else:
        return HttpResponseBadRequest("Error: bad request")

def size(file):
    """This function computes the length of the corpus whose file path is passed as parameter.

        Inputs:
        -file: A string containing the path to the corpus file.
    """
    if (file.endswith(".csv")):
        with open(file, newline='') as csvfile:
            i = len(list(csv.reader(csvfile)))
    else:
        array = np.load(file)
        i = array.shape[0]
    return i


def corpus_size(request, pk):
    corpus = get_object_or_404(Corpus, pk=pk)
    return HttpResponse(corpus.size)

def dim(file):
    """This function computes the dimension of the corpus whose file path is passed as parameter.

        Inputs:
        -file: A string containing the path to the corpus file.
    """
    if (file.endswith(".csv")):
        with open(file, newline='') as csvfile:
            d = len(list(csv.reader(csvfile))[0])
    else:
        array = np.load(file)
        d = array.shape[1]
    return d

def create_csv(file_path, dim):
    """Create a csv file from a stored npy corpus file

        Inputs:
        -file_path:Path to the npy corpus file
        -dim: dimension of the corpus
    """
    array = np.load(file_path)
    file_path = file_path.replace(".csv", ".npy")
    write_csv(file_path, array, dim, 0, np.size(array))


def download(request, pk):
    """ This function send to the client the csv files of the corpus whose pk is passed as parameter.
    If only npy files are present, it also creates the corresponding csv.

        Inputs:
        -request: The HTTP request from the client.
        -pk: The primary key of the corpus to download.
    """
    corpus = get_object_or_404(Corpus, pk=pk)
    corpus_path = os.path.join(
        settings.PATH_TO_USERS_FOLDER + request.user.username, settings.PATH_TO_CORPUS)
    files = [corpus.name.replace(" ", "_")+"_in.csv",
             corpus.name.replace(" ", "_")+"_out.csv"]
    if not os.path.exists(os.path.join(corpus_path, files[0])):
        create_csv(os.path.join(corpus_path, files[0]), corpus.dim_in)
        create_csv(os.path.join(corpus_path, files[0]), corpus.dim_in)
    s = io.BytesIO()
    zf = zipfile.ZipFile(s, "w")
    zip_subdir = "corpus"
    zip_filename = "%s.zip" % zip_subdir
    for filename in files:
        file_path = os.path.join(corpus_path, filename)
        zip_path = os.path.join(zip_subdir, filename)
        zf.write(str(file_path), str(zip_path))
    zf.close()
    resp = HttpResponse(
        s.getvalue(), content_type="application/x-zip-compressed")
    resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename
    return resp


def create(request):
    """This function creates a new corpus and save it into the database after receiving a request (containing a form) from
    the client.

        Inputs:
        -request: The HTTP request from the client.
    """
    if request.method == 'POST':
        form = CorpusForm(request.POST)
        if form.is_valid():
            new_corpus = form.save(commit=False)
            new_corpus.owner = request.user
            new_corpus.size = 0
            new_corpus.dim_in = 0
            new_corpus.dim_out = 0
            new_corpus.path = os.path.join(settings.PATH_TO_USERS_FOLDER + request.user.username,
                                           settings.PATH_TO_CORPUS) + new_corpus.name.replace(" ", "_")
            data_in_name = request.FILES['data_in'].name
            data_out_name = request.FILES['data_out'].name
            if (data_in_name.endswith('.csv') or data_out_name.endswith('.csv')):
                with open(new_corpus.path+"in.csv", 'wb+') as destination:
                    for chunk in request.FILES['data_in'].chunks():
                        destination.write(chunk)
                with open(new_corpus.path+"out.csv", 'wb+') as destination:
                    for chunk in request.FILES['data_out'].chunks():
                        destination.write(chunk)
                if (correct(new_corpus.path+"out.csv") and correct(new_corpus.path+"in.csv") and (size(new_corpus.path+"in.csv") == size(new_corpus.path+"out.csv"))):
                    new_corpus.save()
                    handle_uploaded_data(new_corpus.path+"out.csv", new_corpus.path+"in.csv",
                                        request.user.username, new_corpus.path + "_" + str(new_corpus.pk))
                else:
                    return HttpResponseBadRequest('Error: Form is not valid')
            else:
                with open(new_corpus.path+"in.npy", 'wb+') as destination:
                    for chunk in request.FILES['data_in'].chunks():
                        destination.write(chunk)
                with open(new_corpus.path+"out.npy", 'wb+') as destination:
                    for chunk in request.FILES['data_out'].chunks():
                        destination.write(chunk)
            new_corpus.size = size(new_corpus.path+"in"+os.path.splitext(data_in_name)[1])
            new_corpus.dim_in = dim(new_corpus.path+"in"+os.path.splitext(data_in_name)[1])
            new_corpus.dim_out = dim(new_corpus.path+"out"+os.path.splitext(data_in_name)[1])
            new_corpus.path = new_corpus.path + "_" + str(new_corpus.pk)
            new_corpus.save()
            messages.info(request, 'Corpus successfully created!')
            return HttpResponseRedirect('/accounts/')
        else:
            forms = get_basic_forms(request)
            forms["corpus_form"] = form
            return render(request, 'ARNN/index.html', forms)

def delete(request, pk):
    """ This function deletes a corpus from the database after receiving a request
    from the database.
network
        Inputs:
        -request: The HTTP request from the client.
        -pk: The primary key of the corpus to download.
    """
    corpus = get_object_or_404(Corpus, pk=pk)
    delete_corpus_data(request.user.username, corpus.name.replace(" ", "_"))
    corpus.delete()
    messages.info(request, 'Corpus successfully deleted!')
    return HttpResponseRedirect('/accounts/')


def liste(request):
    """ This function returns a JSON-formatted list of the corpora stored in the database.

        Inputs:
        -request: The HTTP request from the client.
    """
    corpus = Corpus.objects.filter(owner=request.user)
    corp_json = serializers.serialize('json', corpus)
    return HttpResponse(corp_json, content_type='json')

def get_dims(request, pk):
    corpus = get_object_or_404(Corpus, pk=pk)
    return HttpResponse([corpus.dim_in, corpus.dim_out])