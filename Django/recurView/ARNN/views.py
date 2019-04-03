from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import login, logout
from django.views.decorators.csrf import csrf_exempt
from ARNN.forms import RegistrationForm, NetworkForm, TemplateForm, CorpusForm, TaskForm, ObservableForm, CorpusGenerateForm
from django.shortcuts import render, redirect, resolve_url
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from ARNN.models import Corpus
from django.contrib.auth.models import User
import os

@login_required
def index(request):
    return render(request, "ARNN/index.html", get_basic_forms(request))

@login_required
def get_basic_forms(request):
    corpus_form = CorpusForm()
    corpus_generate_form = CorpusGenerateForm()
    template_form = TemplateForm()
    network_form = NetworkForm(user=request.user)
    task_form= TaskForm(user=request.user)
    observable_form = ObservableForm(initial={"periodicity": "1"})
    return {'corpus_form': corpus_form, 'corpus_generate_form': corpus_generate_form, 'template_form': template_form, 'network_form': network_form, 'task_form': task_form, 'observable_form': observable_form}

def signup(request):
    if request.method =='POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            if not(os.path.exists(settings.PATH_TO_USERS_FOLDER)):
                os.mkdir(settings.PATH_TO_USERS_FOLDER)
            user_path = os.path.join(settings.PATH_TO_USERS_FOLDER, user.username)
            os.mkdir(user_path)
            os.mkdir(os.path.join(user_path, settings.PATH_TO_NETWORKS))
            os.mkdir(os.path.join(user_path, settings.PATH_TO_CORPUS))

            login(request, user)
            messages.success(request, 'Your account has been created.')
            return redirect('/accounts/')
    else:
        form = RegistrationForm()

    context = {'form' : form}
    return render(request, 'ARNN/signup.html', context)

def home(request):
    template = loader.get_template('home.html')
    return HttpResponse(template.render({}, request))