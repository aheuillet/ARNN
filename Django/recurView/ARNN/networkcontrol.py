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


class NetworkRunControl(View):
    """This class stores all the networks that are running for a specific django session and control them.
    It is a View based on classe from django that controls the networks accessibles from the client.
    It uses an other class , **networkrunner** wich is located in network.py."""

    #: The class variable 'networks' is a dictionnary that contains all the networkrunners currently loaded.
    #: The user and the name of the network are the keys to a networkerunner.
    networks = dict()
    # the 'plots' class varibles contains the JS script and HTML code to send to the view in order to display the Bokeh graphs
    plots = dict()

    @csrf_exempt
    def get(self, request):
        """ The get fonction is a Django-needed fonction that communicate with the JS via Ajax call.
            It allow the JS of the client to order something to the controller by sending a request with the action and the parameters to apply.

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
                # : This line allow to compress the code by directly executing the command passed by request
                return getattr(self, toexec)(request, user, network_ID)
        else:
            return HttpResponseForbidden("not logged")

    def delete_plot(request, network_ID, plotID):
        user=request.user.username
        if(plotID in self.plots[user.username][network_ID]):
            del self.networks[user.username][network_ID][plotID]
            return HttpResponse()
        return HttpResponseNotFound()

    def get_network_info(self, request, user, network_ID):
        if not (self.exist_entry(user.username, network_ID)):
            messages.error(request, "This network doesn't exist")
            return HttpResponseBadRequest("This network doesn't exist")
        else:
            template = get_object_or_404(Network, pk=network_ID).template
            data = {}
            for a in Template._meta.get_fields():
                b = str(a).replace("ARNN.Template.", "")
                if (b != '<ManyToOneRel: ARNN.network>') and (b != 'id') and (b != 'name') and (b != 'owner') and (b != 'creation_date') and (b != 'last_modified'):#ignore all the field that don't concern the user
                    data[Template._meta.get_field(b).verbose_name] = str(getattr(template, b))

            return JsonResponse(data, safe=False)


    def re_roll_observables(self, request, user, network_ID):
        if not (self.exist_entry(user.username, network_ID)):
            messages.error(request, "This network doesn't exist")
            return HttpResponseBadRequest("This network doesn't exist")
        else:
            for obs in self.networks[user.username][network_ID].calculated_obs:
                print(obs)
                self.networks[user.username][network_ID].calculated_obs[obs] = [[], []]
            self.networks[user.username][network_ID].compute_all_observables(0)
            return HttpResponse('reloaded')

    def get_plots(self, request, network_ID):
        user=request.user.username
        if(user in self.plots and network_ID in self.plots[user]):
            return render(request, "ARNN/bokeh.html", {'plots': self.plots[user][network_ID]})
        return HttpResponse()

    def get_loaded_nets(self, user):
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
            -network_ID :  A string containing the id of the network, with user, allow to identify the network in the database.
        """

        if not (self.exist_entry(user.username, network_ID)):
            messages.error(request, "This network doesn't exist")
            return HttpResponseBadRequest("This network doesn't exist")
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
            -network_ID :  A string containing the id of the network, with user, allow to identify the network in the database.

            Outputs:
            if the observables can be found, the function returns a json containing the observable, otherwise, an error.
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

            return JsonResponse(data2, safe=False)



    def exist_entry(self, username, network_ID):
        """Check if a network is loaded

            Inputs:
            -user : A string containing the name of the owner of the network.
            -network_ID :  A string containing the id of the network, with user, allow to identify the network in the dictionnary networks.
        """
        return (username in self.networks) and (network_ID in self.networks[username])

    def add_user_tab(self, username):
        """Add a new user entry inside of networks if not already in

            Inputs:
            -user : A string containing the name of the owner of the network.
        """
        if not (username in self.networks):
            self.networks[username] = dict()

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
            -network_ID :  A string containing the id of the network, with user, allow to identify the network in the data base.
            -size : The size of the network you are trying to add.

            Outputs:
            If the network is added succesfully, the function returns True, False otherwise.
        """
        if ((self.count_neuron(username) + size) > settings.MAX_NEURONE):
            return 1
        if not (self.exist_entry(username, network_ID)):
            self.networks[username][network_ID] = None
            return 0
        return 2

    def load_network(self, request, user, network_ID, auto_load = False):
        """Load a new network inside of networks if the network can be loaded from the data base.
            If the same user is already using to much resources, the function is not successfull.
            If it is the first time the user load a network, the user is added as an entry inside of networks.

            Inputs:
            -request: HTTP request from the front-end.
            -user : A string containing the name of the owner of the network.
            -network_ID :  A string containing the id of the network, with user, allow to identify the network in the data base.
        """
        self.add_user_tab(user.username)

        network = net.NetworkRunner.load_network(user.username, network_ID, auto_load)
        err = self.add_network_tab(user.username, network_ID, network.network.N)
        if err == 0:
            self.networks[user.username][network_ID] = network
            return HttpResponse('loaded')
        elif err == 1:
            messages.error(request, "Too many neurones already loaded")
            return HttpResponseBadRequest("Too many neurones already loaded")
        else:
            messages.error(request, "Network already loaded")
            return HttpResponseBadRequest('Network already loaded')


    def add_task(self, request, user, network_ID, corpus_ID, start, stop, task):
        """Add a new (testing or training task) to perform to the network.
            Fails if the network isn't loaded.

            Inputs:
            -request: HTTP request from the front-end.
            -user : A string containing the name of the owner of the network.
            -network_ID : A string containing the id of the network, with user, allow to identify the network in the dictionnary networks.
            -corpusname : The name of the corpus to load that is already uploaded on the server.
            -start : An intenger that represent the line of the corpus where to begin the task.
            -stop : An intenger that represent the line of the corpus where to stop the task.
            -task : The type of task that the network shall perform

        """
        if not (self.exist_entry(user.username, network_ID)):
            return HttpResponseBadRequest("The network isn't loaded")
        else:
            CorpusObject = get_object_or_404(Corpus, pk=corpus_ID)
            if (CorpusObject.size <= int(stop)):
                return HttpResponseBadRequest("The stop point must be low than the corpus size")
            if (int(start) < 0):
                return HttpResponseBadRequest("The start point must be greater than 0")
            if self.networks[user.username][network_ID].add_task(CorpusObject.path, int(start), int(stop), task):
                messages.info(request, 'task successfully added')
                return HttpResponseRedirect('/accounts/')
            return HttpResponseBadRequest("The task couldn't be added")


    def add_observable(self, request, user, network_ID, observable, periodicity):
        """Add a new observable for the network to compute and link it to a free Bokeh instance.
            Fails if the network isn't loaded.

            Inputs:
            -request: HTTP request from the front-end.
            -user : A string containing the name of the owner of the network.
            -network_ID : A string containing the id of the network, with user, allow to identify the network in the dictionnary networks.
            -observable : The name of the observable to compute
            -periodicity : This integer tells how many iterations they are between 2 computations of the observable
        """
        if not (self.exist_entry(user.username, network_ID)):
            messages.error(request, "The network doesn't exist")
            return HttpResponseBadRequest("Network doesn't exist")
        else:
            if (user.username not in self.plots):
                self.plots[user.username] = dict()
            if (network_ID not in self.plots[user.username]):
                self.plots[user.username][network_ID] = []
            if (len(self.plots) < settings.MAX_BOKEH):
                print("coucou plot")
                self.networks[user.username][network_ID].add_observable(observable, int(periodicity))
                self.plots[user.username][network_ID].append({'plot': make_ajax_plot(observable, self.networks[user.username][network_ID].size_observable(observable), network_ID), 'name':"bokeh_" + str(len(self.plots)), 'verbose_name': observable})
                return render(request, 'ARNN/bokeh.html', {'plots': self.plots[user.username][network_ID]})
            else:
                messages.error(request, "Unable to add additional Bokeh instance, max limit reached!")
                return HttpResponseBadRequest("Unable to add additional Bokeh instance, max limit reached!")

    def remove_network(self, request, user, network_ID):
        """Remove the corresponding network from networks.

            Inputs:
            -request: HTTP request from the front-end.
            -user : A string containing the name of the owner of the network.
            -network_ID :  A string containing the id of the network, with user, allow to identify the network in the dictionnary networks.
        """
        if self.exist_entry(user.username, network_ID):
            del self.networks[user.username][network_ID]
            del self.plots[user.username][network_ID]
            return HttpResponse()

        messages.error(request, "This network doesn't exist")
        return HttpResponseBadRequest("This network doesn't exist")

    def toggle_run(self, request, user, network_ID):
        """If the corresponding network is not already performing a task, this function launch the iterations of the network from the current step.
            If the network is running, this function stops the task at the current step.

            Inputs:
            -request: HTTP request from the front-end.
            -user : A string containing the name of the owner of the network.
            -network_ID :  A string containing the id of the network, with user, allow to identify the network in the dictionnary networks.
        """
        net = self.networks[user.username][network_ID]
        if (net.threaded):
            net.play_pause()
        else:
            net.start()
        return HttpResponse()

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
            new_network.save()
            net.NetworkRunner.create(request.user.username, new_network.pk)
            messages.info(request, 'Network successfully created!')
            net_json = serializers.serialize('json', [new_network,])
            return HttpResponse(net_json, content_type='json')
        else:
            forms=get_basic_forms(request)
            forms["network_form"]=form
            return render(request, 'ARNN/index.html', forms)

    return HttpResponseBadRequest('Error: Not a POST request')

def edit(request, pk=None):  #FIXME work in progress
    network = get_object_or_404(Network, pk=pk)
    if request.method == 'POST':
        form = NetworkForm(request.user, request.POST, instance=network)
        if form.is_valid():
            new_network = form.save(commit=False)
            new_network.save()
            messages.info(request, 'Network successfully edited!')
            return HttpResponseRedirect('/accounts/')
        else:
            messages.error(request, 'Error: Form is not valid')
            return HttpResponseBadRequest('Error: Form is not valid')
    return HttpResponseBadRequest('Error: Not a POST request')

def list_net(request):
    """ This function return this list of networks owned by the current user as a JSON.

            Inputs :
            -request: HTTP request from the front-end.
    """
    networks = Network.objects.filter(owner=request.user)
    net_json = serializers.serialize('json', networks)
    return HttpResponse(net_json, content_type='json')



def delete(request, pk):
    """ This fonction delete a network from the data base.

            Inputs:
            -request : HTTP request from the front-end
            -pk : the ID of the network to delete
    """
    network = get_object_or_404(Network, pk=pk)
    network.delete()
    path = os.path.join(os.path.join(settings.PATH_TO_USERS_FOLDER, request.user.username), settings.PATH_TO_NETWORKS)
    file = os.path.join(path, str(pk)+"W.npy")
    os.remove(file)
    file = os.path.join(path, str(pk)+"Win.npy")
    os.remove(file)
    file = os.path.join(path, str(pk)+"Wout.npy")
    os.remove(file)
    messages.info(request, 'Network successfully deleted!')
    return HttpResponseRedirect('/accounts/')
