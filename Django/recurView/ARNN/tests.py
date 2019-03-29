import os
import sys
sys.path.insert(0, os.path.abspath('..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recurView.settings")
import django
django.setup()


from ARNN import network
from django.test import TestCase
import numpy as np
import shutil
from recurView import settings


# Create your tests here.
class NetworkRunnerTestCase(TestCase):

    def setup(self):
        self.network = network.NetworkRunner(10, 5, 5, 5, 0.5)


    def test_add_observable(self):
        self.setup()

        self.network.add_observable("observable", 1)
        self.assertTrue(self.network.obs_list[0][0] == "observable")
        self.assertTrue(self.network.obs_list[0][1] ==  1)

        #self.network.add_observable("observable", 2)
        #self.assertTrue(self.network.obs_list[0][1] == 2)
        #self.assertTrue(len(self.network.obs_list) < 2 )


    def test_remove_observable(self):
        self.setup()

        self.network.remove_observable("observable")
        self.assertTrue(len(self.network.obs_list) == 0)

        self.network.obs_list.append(["observable", 0])
        self.network.remove_observable("observable")
        self.assertTrue(len(self.network.obs_list) == 0)


    def test_delete_observable(self):
        self.setup()

        self.assertTrue(len(self.network.calculated_obs) == 0)

        self.network.calculated_obs["observable"] = 1
        self.network.delete_observable("observable")
        self.assertTrue(len(self.network.calculated_obs) == 0)


    def test_add_task(self):
        self.setup()

        output = np.random.rand(self.network.network.N, self.network.dim_output)
        input = np.random.rand(self.network.network.N, self.network.dim_output)
        path = os.path.join(os.path.join(
            settings.PATH_TO_USERS_FOLDER, "test"), settings.PATH_TO_CORPUS)
        file = os.path.join(path, "cortest")
        os.makedirs(os.path.join(
            settings.PATH_TO_USERS_FOLDER, "test"), mode=0o700, exist_ok=True)
        os.makedirs(os.path.join(os.path.join(
            settings.PATH_TO_USERS_FOLDER, "test"), settings.PATH_TO_CORPUS), mode=0o700, exist_ok=True)
        np.save(file + "_in.npy", input)
        np.save(file + "_out.npy", output)

        #check if the network has been trained before runing
        self.assertFalse(self.network.add_task(file, 0, 0, "Test"))

        # we can't add a task to a running network
        self.network.play = True
        open(file, "w+")
        self.assertFalse(self.network.add_task(file, 0, 0, "test task"))

        self.network.play = False
        self.assertTrue(self.network.add_task(file, 0, 0, "Train"))

        # check if the corpus size fits with network dimensions
        output = np.random.rand(self.network.network.N, self.network.network.N)
        input = np.random.rand(self.network.network.Win.shape[0], self.network.network.Win.shape[1])
        np.save(file + "_in.npy", input)
        np.save(file + "_out.npy", output)
        self.assertFalse(self.network.add_task(file, 0, 0, "Test"))

        #shutil.rmtree(os.path.join(settings.PATH_TO_USERS_FOLDER, "test"))


    def test_save(self):
        self.setup()

        output = np.random.rand(self.network.network.N, self.network.network.N)
        input = np.random.rand(self.network.network.Win.shape[1], self.network.network.Win.shape[0])
        weight = np.random.rand(self.network.network.W.shape[1], self.network.network.W.shape[0])
        path = os.path.join(os.path.join(
            settings.PATH_TO_USERS_FOLDER, "test"), settings.PATH_TO_NETWORKS)
        file = os.path.join(path, "nettest.npy")
        os.makedirs(os.path.join(
            settings.PATH_TO_USERS_FOLDER, "test"), mode=0o700, exist_ok=True)
        os.makedirs(os.path.join(os.path.join(
            settings.PATH_TO_USERS_FOLDER, "test"), settings.PATH_TO_NETWORKS), mode=0o700, exist_ok=True)
        open(file, "w+")
        data = np.array([output, input, weight])
        np.save(file, data)
        self.network.network.Wout, self.network.network.Win, self.network.network.W = np.load(file)
        for i in range(len(self.network.network.Wout)):
            for j in range(len(self.network.network.Wout[i])):
                self.assertTrue(self.network.network.Wout[i][j] == output[i][j])
        for i in range(len(self.network.network.Win)):
            for j in range(len(self.network.network.Win[i])):
                self.assertTrue(self.network.network.Win[i][j] == input[i][j])
        for i in range(len(self.network.network.W)):
            for j in range(len(self.network.network.W[i])):
                self.assertTrue(self.network.network.W[i][j] == weight[i][j])
        shutil.rmtree(os.path.join(settings.PATH_TO_USERS_FOLDER, "test"))

    def test_load_template(self):
        self.setup()

        newNetwork = self.network.load_template(0) # template_id=0 : cf migration 0018
        self.assertTrue(newNetwork.network.N == 10)
        self.assertTrue(newNetwork.dim_input == 3)
        self.assertTrue(newNetwork.dim_output == 4)
        newNetwork2 = network.NetworkRunner(N=10, spectral_radius=5, dim_input=3, dim_output=4, proba=0.5, seed = 10, lr=0.5)
        for i in range(newNetwork.network.W.shape[0]):
            for j in range(newNetwork.network.W.shape[1]):
                self.assertTrue(newNetwork.network.W[i][j] == newNetwork2.network.W[i][j])
        for i in range(newNetwork.network.Win.shape[0]):
            for j in range(newNetwork.network.Win.shape[1]):
                self.assertTrue(newNetwork.network.Win[i][j] == newNetwork2.network.Win[i][j])

    def test_load_network(self):
        


    def all_tests(self):
        self.test_add_observable()
        self.test_remove_observable()
        self.test_delete_observable()
        self.test_add_task()
        self.test_save()
        self.test_load_template()
        self.test_load_network()


test = NetworkRunnerTestCase()
test.all_tests()

# 1] go to lab OK
# 2] luminance remaping, mappage de la source vers la target [Hertzmann et al. 2001]
# 3] faire la jittered grid, environ 200 points
# 4] on match entre les points de la grid et de l'image target les points, en fonction de la distance entre les deux vecteurs (vecteurs // à la luminance et luminance du voisinage):
#The neighborhood statistics are precomputed over the image
#and consist of the standard deviation of the luminance values of the
#pixel neighborhood. We have found that a neighborhood size of
#5x5 pixels works well for most images.
# the best matching color sample is selected based on the
# weighted average of luminance (50%) and standard deviation
# (50%).

# 5] revenir en rgb
