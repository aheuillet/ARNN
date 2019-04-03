from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views import View
from django.shortcuts import redirect, render, get_object_or_404, get_list_or_404
from django.conf import settings
from django.core import serializers
from django.contrib import messages
from .models import Template
from .forms import TemplateForm
from .views import get_basic_forms


def create(request):
    """This function creates a new template and save it into the database after receiving a request (containing a form) from
    the client.

        Inputs:
        -request: The HTTP request from the client.
    """
    if request.method == 'POST':
        form = TemplateForm(request.POST)
        if form.is_valid():
            new_template = form.save(commit=False)
            new_template.owner = request.user
            new_template.save()
            messages.info(request, 'Template successfully created!')
            return HttpResponseRedirect('/accounts/')

        forms = get_basic_forms(request)
        forms["template_form"] = form
        return render(request, 'ARNN/index.html', forms)


def download(request, pk):
    """ This function send to the client the csv files of the template whose pk is passed as parameter.

        Inputs:
        -request: The HTTP request from the client.
        -pk: The primary key of the corpus to download.
    """
    template = get_object_or_404(Template, pk=pk)
    data = {}
    for a in Template._meta.get_fields():
        b = str(a).replace("ARNN.Template.", "")
        # ignore all the field that don't concern the user
        if (b != '<ManyToOneRel: ARNN.network>') and (b != 'id') and (b != 'name') and (b != 'owner') and (b != 'creation_date') and (b != 'last_modified'):
            data[Template._meta.get_field(b).verbose_name] = str(getattr(template, b))
    response = JsonResponse(data)
    response['Content-Disposition'] = 'attachment; filename='+ '"' + template.name.replace(" ", "_") + ".json" + '"'
    return response

def delete(request, pk):
    """ This function deletes a template from the database after receiving a request
    from the database.

        Inputs:
        -request: The HTTP request from the client.
        -pk: The primary key of the corpus to download.
    """
    template = get_object_or_404(Template, pk=pk)
    template.delete()
    messages.info(request, 'Template successfully deleted!')
    return HttpResponseRedirect('/accounts/')


def list(request):
    """ This function returns a JSON-formatted list of the templates stored in the database.

        Inputs:
        -request: The HTTP request from the client.
    """
    templates = Template.objects.filter(owner=request.user)
    temp_json = serializers.serialize('json', templates)
    return HttpResponse(temp_json, content_type='json')
