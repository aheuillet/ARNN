from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.views import View
from django.shortcuts import redirect, render, get_object_or_404, get_list_or_404
from django.conf import settings
from django.core import serializers
from django.contrib import messages
from .models import Template
from .forms import TemplateForm
from .views import get_basic_forms

def create(request):
    if request.method == 'POST':
        form = TemplateForm(request.POST)
        if form.is_valid():
            new_template = form.save(commit=False)
            new_template.owner = request.user
            new_template.save()
            messages.info(request, 'Template successfully created!')
            return HttpResponseRedirect('/accounts/')

        forms=get_basic_forms(request)
        forms["template_form"]=form
        return render(request, 'ARNN/index.html', forms)

def edit(request, pk):
    template = get_object_or_404(Template, pk=pk)
    if request.method == 'POST':
        form = TemplateForm(request.POST, instance=template)
        if form.is_valid():
            new_template = form.save(commit=False)
            new_template.save()
            messages.info(request, 'Template successfully edited!')
            return HttpResponseRedirect('/accounts/')
        else:
            return HttpResponseBadRequest('Error: Form is not valid')

    return HttpResponseBadRequest()


def delete(request, pk):
    template = get_object_or_404(Template, pk=pk)
    template.delete()
    messages.info(request, 'Template successfully deleted!')
    return HttpResponseRedirect('/accounts/')

def list(request):
    templates = Template.objects.filter(owner=request.user)
    temp_json = serializers.serialize('json', templates)
    return HttpResponse(temp_json, content_type='json')