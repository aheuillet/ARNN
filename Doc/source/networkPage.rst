.. _Index:

Network Page
============

Once the user is authenticated, the network page is automatically loaded.

.. image:: /image/index.png

Some features are noticeable. First of all, if the button at the top right corner is pressed, some options are displayed.

The homepage can be accessed by clicking on the brain picture at the top left.

If the web browser window is closed, then the current cookies are not cleared so that the user is still logged in. As a consequence the network page can be accessed again by clicking on *Networks* in the homepage, see the :ref:`User`.

The administration system is reachable by clicking on *Welcome* then *Administration*, however you have to be logged in as a superuser to access the page, see :ref:`Admin` chapter for more details. If a user clicks on despite non-superuser privileges, then the administration login page with an error message is displayed.

Networks
++++++++

This part develop the way to concretely use the application.

A user with session cookies has to create a template at first by clicking on *Templates* then *New Template*. A window pops up.

.. image:: /image/template.png

Input *N* is the number of neurons within the reservoir, the *spectral radius* is about the matrix of the connection weigths and the *probability of a connection* concerns the reservoir of neurons. The weight matrix is generated from the seed so that the user can chose to obtain the same one multiple times. It is set by default to *-1* by default which means the Python clock is used to produce the matrix, therefore it is supposed to be random. The *Input Scaling* concerns the rate of significiance of the input matrix in the echo state network state.

The *List* tab allows a logged-in user to download or delete the templates. Download a template provides a JSON file.

Once the session includes at least one template, the user can create a network by clicking on *Networks* then *New Network*.

.. image:: /image/network.png

The selected template will be the network's basis. The networks can be loaded by clicking on *Networks* then *List/Load*. The networks of the session are displayed and the *load*, *delete* and *download* options can be seen. Download a network provides an archive containing three NPY files representing the input, output and weight matrix. When *load* is pressed, the selected network appears at the core with its characteristic in the *Information block* at the left.

.. image:: /image/loaded.png

Afterward a corpus can be generated, by clicking on *Corpus* then two options are available. A corpus can be uploaded from two different files, the two matrix relevant to the input and the ouput in CSV format. Yet, note that the corpus dimensions have to fit the selected dimensions of the network template.

.. image:: /image/corpus.png

An option provides the generation of corpora for *shape-tracking*, as a consequence the *Dimension of output* of the network has to set to 1 and the *Number of columns* has to to fit the *Dimension of input*.

.. image:: /image/corpus_generation.png

When all of this is complete, the current network can be run under several otpions, click on *Add Task* from *Settings* on the right side.

.. image:: /image/task.png

Even if no corpus has been added to the account, *MackeyGlass* corpus is available for everyone.

Either test or training mode can be launched with the corpus whose data is loaded. The steps will be described in the Network Control section.

Download a corpus provides a CSV file.

Network Control
+++++++++++++++

First, at least one *Training task* has to be assigned to the network in order to create an output matrix associated. If the network is saved then reloaded, it can directly be launch with a *Test* task. A *Test task* has to be lauched with every *Training task*, otherwise it fails.

Once a task is assigned to the network, *Observables* can be added, by click on *Add Observable*, in order to plot graphs corresponding to the data of the current network whose the selection can be carried out by clicking in the right tab. Each observable elicits a GUI.

.. image:: /image/gui.png

Lastly, the network can be run by clicking on the play button, and some pieces of data are plot in the Bokeh windows.

.. image:: /image/run.png

The graphic windows at the core is generate by *Bokeh*, which includes somes options their website features in the :ref:`Links`, which can also be opened up by clicking on the *Bokeh* logo on the toolbar. On the settings area, the loop enables repeat of the last task.

The user can close the GUI windows if they are judged annoying.

.. image:: /image/observable.png

The data to be displayed can be chosen and the periodicity of the plot has to be specified. As several graphs may be needed to be displayed, some graphic windows are available to the user.
