# -*- coding: utf-8 -*-
#!/usr/bin/env python -W ignore::DeprecationWarning
import numpy as np
from .reservoirpy import mat_gen
from .reservoirpy import ESN
import json
import os
from threading import Event, Thread, Lock
from django.db import models
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import Template, Network
from datetime import date
from recurView import settings
import time
from .reservoirpy.observables import get_spectral_radius, compute_error_NRMSE


class NetworkRunner():
    """This classe intances correspond to a running network. They use the ESN classe to run the network during a task.
        The saving of the matrix of the ESN allow persistency across re-loading of the network.
        The caracteristics of the network are stored inside of the django database.
    """

    def __init__(self, N, spectral_radius, dim_input, dim_output, proba, input_bias=True, seed=None, lr=0.3, IS = None):
        # threading.Thread.__init__(self)
        if (seed == -1 or seed is None):
            seed = int(time.time()) % 1000
        self.ready = Event()  #: allows for multi threading
        self.threadLock = Lock()  #: allows for multi threading
        self.play = False
        self.dim_output = dim_output
        self.dim_input = dim_input
        W = mat_gen.generate_internal_weights( N=N, spectral_radius=spectral_radius, proba=proba, seed=seed)
        Win = mat_gen.generate_input_weights(nbr_neuron=N, dim_input=dim_input, input_scaling=IS, proba=proba, input_bias=input_bias, seed=seed)
        self.states = []  #: Contains all the states of the reservoir across testing
        self.input = []  #: Contains all the inputs given to the reservoir across testing
        self.expected_output = [] #: Contains all the corrects ouputs given to the reservoir across testing
        self.predicted_output = [] #: Contains all the ouputs the reservoir computed across testing
        self.calculated_obs = dict() #: A dictionnary of all the observables that are already computed
        self.network = ESN.ESN(lr, W, Win, input_bias=input_bias, ridge=None, Wfb=None, fbfunc=None)  # the actual network
        self.task_list = []  #: List of trainings and testing to perform
        self.current_task_num = 0
        self.last_iteration = 0
        self.obs_list = []  #: List of observables to compute with their periodicity
        self.pk = -1 #: Primary key of the network in the database

    @staticmethod
    def load_network(username, pk, load_auto_save = False):
        """Loads a network that have already been created and stored in the database.

            Inputs:
            -pk: An int is the primary key of the network entry in the database.
            -username: A string containing the name of the owner of the netxork.
            -load_auto_save: This boolean tells if the auto-saved files should be loaded instead of the regular files.

            Output:
            The networkRunner corresponding to the database entry.
        """
        NetworkObject = get_object_or_404(Network, pk=pk)
        network_path = os.path.join(os.path.join(settings.PATH_TO_USERS_FOLDER, username), settings.PATH_TO_NETWORKS)
        network = NetworkRunner.load_template(NetworkObject.template_id)
        if load_auto_save:
            network.load_matrix(os.path.join(network_path, pk+"~"))        
            NetworkObject.auto_saved = False
            network.save_data(os.path.join(network_path, pk))
        else:
            network.load_matrix(os.path.join(network_path, pk))
            if os.path.exists(os.path.join(network_path, pk+"~")):#remove the auto-saved files
                os.remove(os.path.join(network_path, pk+"~"))
        network.pk = pk
        return network

    def load_matrix(self, path):
        """Sets the atributes of the ESN with the values previously stored on disk. The location of the numpy file
        is computed from path in the setting folder and colunms from the data base.

            Inputs:
            -path: An string that is the path to the files to load.

        """
        self.network.Wout = np.load(path+"Wout.npy")
        self.network.Win = np.load(path+"Win.npy")
        self.network.W = np.load(path+"W.npy")

    @staticmethod
    def load_template(template_id):
        """Loads a template from the database and create a corresponding networkrunner from it. The network
        is created by parsing all the parameters contained in the template that concerns the network.
            Inputs:
            -template_id: An int that is the primary key of the template entry in the database.

            Output:
            The networkRunner corresponding to the template.
        """
        basetemplate = get_object_or_404(Template, pk=template_id)
        s = ""
        for a in Template._meta.get_fields():
            b = str(a).replace("ARNN.Template.", "")
            if (b != '<ManyToOneRel: ARNN.network>') and (b != 'id') and (b != 'name') and (b != 'owner') and (b != 'creation_date') and (b != 'last_modified'):#ignore all the field that don't concern the network's building
                arg = str(getattr(basetemplate, b))#set the value
                s += b+" = "+arg+","
        return eval("NetworkRunner("+s+")")

    @staticmethod
    def load_corpus(path):
        """Loads a corpus stored on disk and returns it.

            Inputs:
            -path: A string that contains the path to a corpus.

            Outputs:
            -inp: An np array that contains all of the inputs of the corpus
            -out: An np array containing the expected outputs for every input
        """
        inp = np.load(path + "_in.npy")
        out = np.load(path + "_out.npy")
        return inp, out

    @staticmethod
    def create(username, network_ID):
        """Create a new network based on the template corresponding to the template_ID and saves it on disk.

            Inputs:
            -username: A string that contains the name of the owner of the network, this allow to
            create the path to the saving file.
            -network_ID: An int that is the primary key to the network.

        """
        newnet = NetworkRunner.load_template(get_object_or_404(Network, pk=network_ID).template.pk)
        newnet.pk = network_ID
        newnet.save(username, network_ID)

    def get_observable(self):
        """Returns the dictionary that contains all the observables computed at this point.

            Output:
            -The attribute "calculated_obs"
        """
        return self.calculated_obs

    def resume_training(self):
        """Runs the ESN over all the tasks set in task_list, if the task is a testing task,
        the input, predicted output, expected output, and the reservoir state's lists are increased
        by the results of the runing. Then the function goes through all the observables to compute
        and compute them, then add them in the calculated_obs list. This function is threaded,
        so if the controller ask to stop the running, the computation stops.
        """
        print(self.play)
        print(self.task_list)
        while(self.play and self.current_task_num < len(self.task_list)): # if the network is launched and the list of task is not over
            if (self.task_list[self.current_task_num][0] == "Train"):#if the task is a training task, the ESN is trained on the data and no other attribute is changed
                self.network.train(inputs=[self.task_list[self.current_task_num][1], ], teachers=[self.task_list[self.current_task_num][2], ], wash_nr_time_step=0, verbose=False)
            elif (self.task_list[self.current_task_num][0] == "Test"):#if the task is a testing task, the ESN is runned ont the data, then the results, the input given and the expected ouputs are added to the respective lists
                outputs, all_in_state = self.network.run(inputs=[self.task_list[self.current_task_num][1], ])
                print(all_in_state)
                for i in range(len(self.task_list[self.current_task_num][1])):#add all information to the respective lists
                    self.input.append(self.task_list[self.current_task_num][1][i])
                    self.expected_output.append(self.task_list[self.current_task_num][2][i])
                    self.predicted_output.append(outputs[0][i])
                    self.states.append(all_in_state[0][i])
            else:
                raise Exception("this task isn't availlable")
            self.current_task_num += 1
            self.compute_all_observables(self.last_iteration)    
            if (self.task_list[self.current_task_num - 1][0] == "test"):
                self.last_iteration += len(self.task_list[self.current_task_num - 1][2])
            self.auto_save()
        self.ready.set()
        self.play = False

    def compute_all_observables(self, begin):
        for i in range(len(self.obs_list)):
                for x in range(begin, len(self.input), self.obs_list[i][1]):
                    self.x = x
                    self.calculated_obs[self.obs_list[i][0]][1].append(self.compute_observable(self.obs_list[i][0]))
                    self.calculated_obs[self.obs_list[i][0]][0].append(x)

    def add_task(self, path, start, stop, task, demo=False):
        """Add a new task to the task_list.

            Inputs:
            -path: A string containing the path to the corpus file
            -start: An int that is the begining of the training sequence inside of the corpus
            -stop: An int that is the end of the training sequence inside of the corpus
            -task: A string that contains the type of task to perform

            Ouputs:
            returns False if it couldn't add the task, True otherwise.
        """
        if (not demo and (task=="Test") and (self.network.Wout.all() == None) and not("Train" in [i[0] for i in self.task_list])):#check if the network has been trained before running
            return False
        if not(self.play):#a task can only be added if the network is not running
            inp, out = self.load_corpus(path)
            if (inp.shape[1] != self.dim_input) or (out.shape[1] != self.dim_output):
                return False
            self.task_list.append([task, inp[start:stop], out[start:stop]])
            return True
        return False

    def play_pause(self):
        """Launch the computation if the network is not running or stop it otherwise"""
        print("plaaaaaay")
        self.threadLock.acquire()
        self.play = not(self.play)
        self.threadLock.release()
        if self.play:
            thread = Thread(target=self.resume_training)
            thread.start()
            self.ready.wait()
        return 'Played'


    def add_observable(self, observable, periodicity): 
        """Add a new observable to compute to the list. If the observable is already in the liste,
        this function only change the periodicity of the computation of the observable.

            Inputs:
            -observable: A string containing the name of the observable to add.
            -periodicity: An int that is the gape between 2 computations of the observable
        """
        if not(observable in self.obs_list):
            self.calculated_obs[observable] = [[], []]
            self.obs_list.append([observable, periodicity])
        else:
            for i in range(len(self.obs_list)):
                if self.obs_list[i][0] == observable:
                    self.obs_list[i][1] = periodicity
                    break

    def remove_observable(self, observable):
        """Removes the entry of the observable in the dictionnary 'obs_list'.
        Input:
        -observable: A string containing the name of the observable to remove
        """
        for i in range(len(self.obs_list)):
            if self.obs_list[i][0] == observable:
                del self.obs_list[i]

    def delete_observable(self, observable):
        """Removes the values from calculated_obs that are related to the observable 'observable'.
        Input:
        -observable: A string containing the name of the observable to remove
        """
        if (observable in self.calculated_obs):
            del self.calculated_obs[observable]

    def compute_observable(self, observable):
        """Compute an observable at a specific point (self.x), using the functions defined in the observable.py file, in /reservoirpy/ folder.

        Input:
        -observable: A string containing the name of the observable to compute.
        Output:
        -A vector containing the asked observable.
        """
        if (observable == "Spectral Radius"):
            return np.array([get_spectral_radius(self.network.W)]).tolist()
        elif (observable == 'Predicted Output'):
            return self.predicted_output[self.x].tolist()
        elif (observable == 'Expected Output'):
            return self.expected_output[self.x].tolist()
        elif (observable == 'Reservoir States'):
            return self.states[self.x].tolist()
        elif (observable == 'Input'):
            return self.input[self.x].tolist()
        elif (observable == 'Rmse'):
            nmrse_mean, nmrse_maxmin, rmse, mse = compute_error_NRMSE(np.array(self.expected_output), np.array(self.predicted_output), False)
            return np.array([rmse]).tolist()
        elif (observable == "Mse"):
            nmrse_mean, nmrse_maxmin, rmse, mse = compute_error_NRMSE(np.array(self.expected_output), np.array(self.predicted_output), False)
            return np.array([mse]).tolist()
        elif (observable == "Nmrse maxmin"):
            nmrse_mean, nmrse_maxmin, rmse, mse = compute_error_NRMSE(np.array(self.expected_output), np.array(self.predicted_output), False)
            return np.array([nmrse_maxmin]).tolist()
        elif (observable == "Nmrse mean"):
            nmrse_mean, nmrse_maxmin, rmse, mse = compute_error_NRMSE(np.array(self.expected_output), np.array(self.predicted_output), False)
            return np.array([nmrse_mean]).tolist()
        return 0

    def size_observable(self, observable):
        """Compute the size of a observable defined in the observable.py file, in /reservoirpy/ folder.

        Input:
        -observable: A string containing the name of the observable to compute.
        Output:
        -The dimension of the asked observable.
        """
        if (observable == "Spectral Radius"):
            return 1
        elif (observable == 'Predicted Output'):
            return self.dim_output
        elif (observable == 'Expected Output'):
            return self.dim_output
        elif (observable == 'Reservoir States'):
            return self.network.N
        elif (observable == 'Input'):
            return self.dim_input
        elif (observable == 'Rmse'):
            return 1
        elif (observable == "Mse"):
            return 1
        elif (observable == "Nmrse maxmin"):
            return 1
        elif (observable == "Nmrse mean"):
            return 1

    def auto_save(self):
        """This function saves all the matrix of a network in tempoary files. 
            It also update the network in the data base to notify that there are unsaved data.
        """
        try :
            net = get_object_or_404(Network, pk=self.pk)
        except :
            print("demo")
        else:
            path = os.path.join(os.path.join(settings.PATH_TO_USERS_FOLDER, str(net.owner.username)), settings.PATH_TO_NETWORKS)
            file = os.path.join(path, str(net.pk)+"~")
            self.save_data(file)
            net.auto_saved = True
            net.save()


    def save(self, username, name):
        """Write a network onto the disk and remove all auto-saved references.

        Input:
        -username: A string containing the name of the owner of the network.
        -name: The name of the network to save.
        """
        path = os.path.join(os.path.join(settings.PATH_TO_USERS_FOLDER, str(username)), settings.PATH_TO_NETWORKS)
        file = os.path.join(path, str(name)) 
        self.save_data(file)       
        net = get_object_or_404(Network, pk=self.pk)
        net.auto_saved = False
        if os.path.exists(file+"~"+"Win.npy"):
            os.remove(file+"~"+"Win.npy")
        if os.path.exists(file+"~"+"W.npy"):
            os.remove(file+"~"+"W.npy")
        if os.path.exists(file+"~"+"Wout.npy"):
            os.remove(file+"~"+"Wout.npy")
        net.save()

    def save_data(self, file):
        """Write a network onto the disk at the location given.

        Input:
        -file: A string containing the path to the network.
        """
        os.makedirs(os.path.dirname(file), mode=0o700, exist_ok=True)
        np.save(file+"Wout.npy", self.network.Wout)
        np.save(file+"Win.npy", self.network.Win)
        np.save(file+"W.npy", self.network.W)

    # def run(self):
    #     """Allow to play/pause the network with threading"""
    #     print("play")
    #     self.threaded = True
    #     return self.play_pause()
