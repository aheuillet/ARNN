# -*- coding: utf-8 -*-
#!/usr/bin/env python -W ignore::DeprecationWarning
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.views import View
from django.shortcuts import redirect, render, get_object_or_404, get_list_or_404
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.conf import settings
from .bokeh import make_ajax_plot
from django.contrib import messages
from .models import Network, Corpus, Template
from .forms import NetworkForm
from . import network as net
import numpy as np
import os
import io
import zipfile


class NetworkRunControl(View):
    """This class stores all the networks that are running for a specific django session and control them.
    It is a View based on classe from django that controls the networks accessibles from the client.
    It uses an other class , **networkrunner** wich is located in network.py."""

    #: The class variable 'networks' is a dictionnary that contains all the networkrunners currently loaded.
    #: The user and the name of the network are the keys to a networkerunner.
    networks = dict()
    #: The 'plots' class variable contains the JS script and HTML code to send to the view in order to display the Bokeh graphs
    plots = dict()
    #: The class variable 'tasks' is a dictionnary that contains all the taks of a network.
    #: The user and the name of the network are the keys to a list of task.
    tasks = dict()

    @csrf_exempt
    def get(self, request):
        """ The get fonction is a Django-needed fonction that communicate with the JS via Ajax call.
            It allows the JS of the client to order something to the controller by sending a request with the action and the parameters to apply.

            Inputs:
            -request : an http request containing a task to perform and some additionnal parameters.
        """
        if request.user.is_authenticated:
            user = request.user
            toexec = request.GET.get("method", None)
            network_ID = request.GET.get("network_ID", None)
            if (toexec == "get_plots"):
                return self.get_plots(request, network_ID)
            elif (toexec == "delete_plot"):
                plotID = request.GET.get("plotID", None)
                return self.delete_plot(request, network_ID, plotID)
            elif (toexec == "get_loaded_nets"):
                return self.get_loaded_nets(user)
            elif (toexec == "add_task"):
                corpusID = request.GET.get("corpusID", None)
                start = request.GET.get("start", None)
                stop = request.GET.get("stop", None)
                task = request.GET.get("task", None)
                return self.add_task(request, user, network_ID, corpusID, start, stop, task)
            elif (toexec == "add_observable"):
                observable = request.GET.get("observable", None)
                periodicity = request.GET.get("periodicity", None)
                return self.add_observable(request, user, network_ID, observable, periodicity)
            elif (toexec == "get_observable"):
                observable = request.GET.get("observable", None)
                return self.get_observable(request, user, observable, network_ID)
            elif (toexec == "list"):
                return self.list_net(request)
            else:
                # This line allows to compress the code by directly executing the command passed by request
                return getattr(self, toexec)(request, user, network_ID)
        else:
            return HttpResponseForbidden("not logged")


    def get_network_tasks(self, request, user, network_ID):
        """ This function allows to build the list of task of a network.
            It allows the JS of the client to build a modal listing all the tasks.

            Inputs:
            -request: HTTP request from the front-end.
            -user : A string containing the name of the owner of the network.
            -network_ID :  A string containing the id of the network, with user, allows to identify the network in the database.

            Ouputs: 
            -A json of the list of dictionnaries, each describing a task.
        """
        if not (self.exist_entry(user.username, network_ID)):
            return HttpResponseBadRequest("This network doesn't exist")
        else:
            return JsonResponse(self.tasks[user.username][network_ID], safe=False)


    def delete_plot(self, request, network_ID, plotID):
        """ This function remove the bokeh component from the class variable 'plots'.

            Inputs:
            -request: HTTP request from the front-end.
            -network_ID :  A string containing the id of the concerned network.
            -plotID :  A string containing the id of the plot, with network_ID, it allows to identify the plot to delete.
        """
        user=request.user.username
        plots=self.plots[user][network_ID]
        for bokeh in plots:
            if bokeh.get('name') == plotID:
                del plots[plots.index(bokeh)]
                return HttpResponse()
        return HttpResponseNotFound()


    def get_network_info(self, request, user, network_ID):
        """ This function allows to build the list of information about a network.
            It allows the JS of the client to build a modal listing all the information oa a network.

            Inputs:
            -request: HTTP request from the front-end.
            -user : A string containing the name of the owner of the network.
            -network_ID :  A string containing the id of the network, with user, allows to identify the network in the database.

            Ouputs: 
            -A json of a dictionnary, describing the network.
        """
        if not (self.exist_entry(user.username, network_ID)):
            return HttpResponseBadRequest("This network doesn't exist")
        else:
            net = get_object_or_404(Network, pk=network_ID)
            template = net.template
            data = {}
            if len(self.networks[user.username][network_ID].predicted_output) > 1:#: If it is possible to compute the error
                data["Nmrse mean"] = self.networks[user.username][network_ID].compute_observable("Nmrse mean")
                data['Rmse'] = self.networks[user.username][network_ID].compute_observable('Rmse')

            for a in Template._meta.get_fields():
                b = str(a).replace("ARNN.Template.", "")
                if (b != '<ManyToOneRel: ARNN.network>') and (b != 'id') and (b != 'name') and (b != 'owner') and (b != 'creation_date') and (b != 'last_modified'):#ignore all the field that don't concern the user
                    data[Template._meta.get_field(b).verbose_name] = str(getattr(template, b))

            return JsonResponse(data, safe=False)


    def re_roll_observables(self, request, user, network_ID):
        """ This function recompute all the observables of a network. 
            It is used to refresh the display of an observable added after the network have been run.

            Inputs:
            -request: HTTP request from the front-end.
            -user : A string containing the name of the owner of the network.
            -network_ID :  A string containing the id of the network, with user, allows to identify the network in 'networks'.
        """
        if not (self.exist_entry(user.username, network_ID)):
            messages.error(request, "This network doesn't exist")
            return HttpResponseRedirect('/accounts/')
        else:
            for obs in self.networks[user.username][network_ID].calculated_obs:
                self.networks[user.username][network_ID].calculated_obs[obs] = [[], []]# Empty the all the observable
            self.networks[user.username][network_ID].compute_all_observables(0)# Compute all the observables
            return HttpResponse('reloaded')


    def get_plots(self, request, network_ID):
        """ This function allows to display the bokeh elements of a network. 
            It is used to display all the observables of a network.

            Inputs:
            -request: HTTP request from the front-end.
            -network_ID :  A string containing the id of the network, it allows to identify the network in the 'plots' class variable.

            Output:
            -A render of the bokeh applied to the observables ploted.
        """
        user=request.user.username
        if(user in self.plots and network_ID in self.plots[user]):
            return render(request, "ARNN/bokeh.html", {'plots': self.plots[user][network_ID]})# Make the actual display of the bokeh
        #messages.error(request, "This network doesn't exist")
        return HttpResponseNotFound("This network doesn't exist")


    def get_loaded_nets(self, user):
        """ Lists all the networks currently loaded by a user.

            Inputs:
            -user : A reference to a user in the database.

            Outputs:
            -A json of a list of all the networks owned by user.
        """
        if (user.username in self.networks):
            nets = Network.objects.filter(owner=user, pk__in=self.networks[user.username])
            net_json = serializers.serialize('json', nets)
            return HttpResponse(net_json, content_type='json')
        return HttpResponse()


    def save_network(self, request, user, network_ID):
        """Save the network inside of the database and on disk, by calling save the function of networkrunner.

            Inputs:
            -request: HTTP request from the front-end.
            -user : A string containing the name of the owner of the network.
            -network_ID :  A string containing the id of the network, with user, it allows to identify the network in 'networks'.
        """

        if not (self.exist_entry(user.username, network_ID)):
            messages.error(request, "This network doesn't exist")
            return HttpResponseRedirect('/accounts/')
        else:
            self.networks[user.username][network_ID].save(user, network_ID)
            messages.info(request, 'Network successfully saved!')
            return HttpResponseRedirect('/accounts/')


    @csrf_exempt
    def get_observable(self, request, user, observable, network_ID):
        """Fetch the observable calculated by the network and associated with the Bokeh instance whose ID is passed as parameter. If calculated and send them to the front end to be displayed.
            If their is no such network running or observable, return an error.

            Inputs:
            -request: HTTP request from the front-end.
            -user : A string containing the name of the owner of the network.
            -observable: A string containing the name of the observable whose comptuted values have to be returned to the client.
            -network_ID :  A string containing the id of the network, with user, allows to identify the network in the 'networks'.

            Outputs:
            -If the observables can be found, the function returns a json containing the observables.
    """
        if not (self.exist_entry(user.username, network_ID)):
            return HttpResponseNotFound('failed')
        else:
            data = self.networks[user.username][network_ID].get_observable()[observable]
            data2 = {
                "x": data[0]
            }
            for i in range(len((list(np.array(data[1]).T)))):
                data2["y"+str(i)] = [float(a) for a in (list(np.array(data[1]).T[i]))]
            print(data2)
            return JsonResponse(data2, safe=False)


    def exist_entry(self, username, network_ID):
        """Check if a network is loaded.

            Inputs:
            -user : A string containing the name of the owner of the network.
            -network_ID :  A string containing the id of the network, with user, allows to identify the network in the dictionnary networks.

            Outputs:
            -True if the network is loaded, false otherwise.
        """
        return (username in self.networks) and (network_ID in self.networks[username])


    def add_user_tab(self, username):
        """Add a new user entry inside of networks if not already in

            Inputs:
            -user : A string containing the name of the owner of the network.
        """
        if not (username in self.networks):
            self.networks[username] = dict()
            self.tasks[username] = dict()
            self.plots[username] = dict()


    def count_neuron(self, username):
        """Count the total number of neurones in all the networks currently loaded by an user.

            Inputs:
            -user : A string containing the name of the owner of the networks.

            Outputs:
            The function return the sum of all the size of the networks that are loaded.
        """
        n = 0
        for i in self.networks[username]:
            n += self.networks[username][i].network.N
        return n


    def add_network_tab(self, username, network_ID, size):
        """Add a new network entry inside of networks if the network can be loaded from the data base.
            If the same user is already using to much resources, the function is not successfull.

            Inputs:
            -user : A string containing the name of the owner of the network.
            -network_ID :  A string containing the id of the network, with user, allows to identify the network in the data base.
            -size : The size of the network you are trying to add.

            Outputs:
            If the network is added succesfully, the function returns 0, if too many neuronnes where already loaded, 1 and 2 if the network was already loaded.
        """
        if ((self.count_neuron(username) + size) > settings.MAX_NEURONE):
            return 1
        if not (self.exist_entry(username, network_ID)):
            self.networks[username][network_ID] = None
            self.tasks[username][network_ID] = []
            self.plots[username][network_ID] = []
            return 0
        return 2


    def load_network(self, request, user, network_ID, auto_load = False):
        """Load a new network inside of networks if the network can be loaded from the data base.
            If the same user is already using to much resources, the function is not successfull.
            If it is the first time the user load a network, the user is added as an entry inside of networks.

            Inputs:
            -request: HTTP request from the front-end.
            -user : A string containing the name of the owner of the network.
            -network_ID :  A string containing the id of the network, with user, allows to identify the network in the data base.
            -auto_load : A boolean value, if True, the auto saved files must be loaded, if False, the network gets loaded normally.
        """
        self.add_user_tab(user.username)

        network = net.NetworkRunner.load_network(user.username, network_ID, auto_load)
        err = self.add_network_tab(user.username, network_ID, network.network.N)
        if err == 0:
            self.networks[user.username][network_ID] = network
            return HttpResponse('loaded')
        elif err == 1:
            messages.error(request, "Too many neurones already loaded")
            return HttpResponseRedirect('/accounts/')
        else:
            messages.error(request, "Network already loaded")
            return HttpResponseRedirect('/accounts/')


    def add_task(self, request, user, network_ID, corpus_ID, start, stop, task):
        """Add a new (testing or training task) to perform to the network.
            Fails if the network isn't loaded.

            Inputs:
            -request: HTTP request from the front-end.
            -user : A string containing the name of the owner of the network.
            -network_ID : A string containing the id of the network, with user, allows to identify the network in the dictionnary networks.
            -corpus_ID : The ID of the corpus to load that is already uploaded on the server.
            -start : An intenger that represent the line of the corpus where to begin the task.
            -stop : An intenger that represent the line of the corpus where to stop the task.
            -task : The type of task that the network shall perform

        """
        if not (self.exist_entry(user.username, network_ID)):
            return HttpResponseBadRequest("The network isn't loaded")
        else:
            CorpusObject = get_object_or_404(Corpus, pk=corpus_ID)
            if (CorpusObject.size <= int(stop)):
                return HttpResponseBadRequest("The stop point must be lower than the corpus size")
            if (int(start) < 0):
                return HttpResponseBadRequest("The start point must be greater or equal to 0")
            if self.networks[user.username][network_ID].add_task(CorpusObject.path, int(start), int(stop), task):
                infos = {
                    "corpus": CorpusObject.name,
                    "type": task,
                    "start": start,
                    "stop": stop
                }
                
                self.tasks[user.username][network_ID].append(infos)# Every time a task is added, the modals of tab needs to be updated
                messages.info(request, 'task successfully added')
                return HttpResponseRedirect('/accounts/')
            messages.error(request, 'error at task creation')
            return HttpResponseBadRequest("The task couldn't be added")


    def add_observable(self, request, user, network_ID, observable, periodicity):
        """Add a new observable for the network to compute and link it to a free Bokeh instance.
            Fails if the network isn't loaded.

            Inputs:
            -request: HTTP request from the front-end.
            -user : A string containing the name of the owner of the network.
            -network_ID : A string containing the id of the network, with user, allows to identify the network in the dictionnary networks.
            -observable : The name of the observable to compute
            -periodicity : This integer tells how many iterations they are between 2 computations of the observable
        """
        if not (self.exist_entry(user.username, network_ID)):
            messages.error(request, "The network doesn't exist")
            return HttpResponseRedirect('/accounts/')
        else:
            if (len(self.plots) < settings.MAX_BOKEH):
                self.networks[user.username][network_ID].add_observable(observable, int(periodicity))
                self.plots[user.username][network_ID].append({'plot': make_ajax_plot(observable, self.networks[user.username][network_ID].size_observable(observable), network_ID), 'name':"bokeh_" + str(len(self.plots[user.username][network_ID])), 'verbose_name': observable})
                return render(request, 'ARNN/bokeh.html', {'plots': self.plots[user.username][network_ID]})# Makes the render of the observable
            else:
                messages.error(request, "Unable to add additional Bokeh instance, max limit reached!")
                return HttpResponseRedirect('/accounts/')


    def remove_network(self, request, user, network_ID):
        """Remove the corresponding network from networks.

            Inputs:
            -request: HTTP request from the front-end.
            -user : A string containing the name of the owner of the network.
            -network_ID :  A string containing the id of the network, with user, allows to identify the network in the dictionnary networks.
        """
        if self.exist_entry(user.username, network_ID):
            del self.networks[user.username][network_ID]
            if (user.username in self.plots) and network_ID in self.plots[user.username]:
                del self.plots[user.username][network_ID]
            return HttpResponse()

        messages.error(request, "This network doesn't exist")
        return HttpResponseRedirect('/accounts/')


    def toggle_run(self, request, user, network_ID):
        """If the corresponding network is not already performing a task, this function launch the iterations of the network from the current step.
            If the network is running, this function stops the task at the current step.

            Inputs:
            -request: HTTP request from the front-end.
            -user : A string containing the name of the owner of the network.
            -network_ID :  A string containing the id of the network, with user, allows to identify the network in the dictionnary networks.
        """
        net = self.networks[user.username][network_ID]
        a = "run ?"
        a = net.play_pause()
        print(a)
        return HttpResponse(a)


def get_network_saved(request, pk):
    """ This function returns a boolean meaning if the network given has some unsaved data.

            Inputs :
            -request: HTTP request from the front-end.
            Outputs :
            -A boolean value
    """
    return HttpResponse(get_object_or_404(Network, pk=pk).auto_saved, content_type='bool')


def create(request):
    """This function create a new network, by generating all the matrix that are inside, and add the corresponding entry inside of the database.

            Inputs:
            -request : HTTP request from the front-end.
    """
    if request.method == 'POST':
        form = NetworkForm(request.user, request.POST)
        if form.is_valid():
            new_network = form.save(commit=False)
            new_network.owner = request.user
            new_network.save()# Create the network in the database
            net.NetworkRunner.create(request.user.username, new_network.pk)
            messages.info(request, 'Network successfully created!')
            net_json = serializers.serialize('json', [new_network,])
            return HttpResponse(net_json, content_type='json')
        else:
            forms=get_basic_forms(request)
            forms["network_form"]=form
            return render(request, 'ARNN/index.html', forms)
    return HttpResponseBadRequest('Error: Not a POST request')


def list_net(request):
    """ This function return this list of networks owned by the current user as a JSON.

            Inputs :
            -request: HTTP request from the front-end.
            Outputs :
            -A json of the list of networks own by a person
    """
    networks = Network.objects.filter(owner=request.user)
    net_json = serializers.serialize('json', networks)
    return HttpResponse(net_json, content_type='json')


def delete(request, pk):
    """ This fonction delete a network from the data base, and from the disk.

            Inputs:
            -request : HTTP request from the front-end
            -pk : the ID of the network to delete
    """
    network = get_object_or_404(Network, pk=pk)
    network.delete()
    path = os.path.join(os.path.join(settings.PATH_TO_USERS_FOLDER, request.user.username), settings.PATH_TO_NETWORKS)
    file = os.path.join(path, str(pk)+"W.npy")
    if os.path.exists(file):
        os.remove(file)
    file = os.path.join(path, str(pk)+"Win.npy")
    if os.path.exists(file):
        os.remove(file)
    file = os.path.join(path, str(pk)+"Wout.npy")
    if os.path.exists(file):
        os.remove(file)
    file = os.path.join(path, str(pk)+"~W.npy")
    if os.path.exists(file):
        os.remove(file)
    file = os.path.join(path, str(pk)+"~Win.npy")
    if os.path.exists(file):
        os.remove(file)
    file = os.path.join(path, str(pk)+"~Wout.npy")
    if os.path.exists(file):
        os.remove(file)
    messages.info(request, 'Network successfully deleted!')
    return HttpResponseRedirect('/accounts/')


def download(request, pk):
    """ This function creates a ZIP archive containing the NPY files (weight matrix and state matrix)
        of the network whose primary key is passed as parameter.

        Inputs:
        -request: HTTP request from the front-end
        -pk: The ID of the network whose NPY files need to be downloaded.
    """
    network = get_object_or_404(Network, pk=pk)
    network_path = os.path.join(settings.PATH_TO_USERS_FOLDER + request.user.username, settings.PATH_TO_NETWORKS)
    files = [str(network.pk)+"Win.npy", str(network.pk)+"Wout.npy", str(network.pk)+"W.npy"]
    s = io.BytesIO() 
    zf = zipfile.ZipFile(s, "w")
    zip_subdir = network.name
    zip_filename = "%s.zip" % zip_subdir
    for filename in files:
        fpath = os.path.join(network_path, filename)
        zip_path = os.path.join(zip_subdir, filename)
        zf.write(fpath, zip_path)
    zf.close()
    resp = HttpResponse(s.getvalue(), content_type = "application/x-zip-compressed")
    resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename
    return resp

def get_dims(request, pk):
    network = get_object_or_404(Network, pk=pk)
    return HttpResponse([network.template.dim_input, network.template.dim_output])