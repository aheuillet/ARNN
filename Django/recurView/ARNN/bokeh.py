from django.shortcuts import render, redirect, resolve_url
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from bokeh.plotting import figure
from bokeh.resources import CDN
from django.conf import settings
from bokeh.embed import components
from bokeh.models.sources import AjaxDataSource
from .network import NetworkRunner
import os
from django.db import models
from django.shortcuts import get_object_or_404
from .models import Template, Network

net = NetworkRunner( N=100, spectral_radius=10, dim_input=1, dim_output=1, proba=0.1, seed = 42)

def make_ajax_plot(observable, network_ID):
    """This function is used to create a new Bokeh instance to send to the view.

        Inputs:
        -observable: a string containing the name of the observable to poll for.
        -network_ID: an int referring to the network whose observable need to be fetched.
    """
    source = AjaxDataSource(method='GET', data_url=resolve_url('control') + "?method=get_observable&observable=" + str(observable) + "&network_ID=" + str(network_ID),
                            polling_interval=3000, mode='replace')
    source.data = dict(x=[], y=[])

    plot = figure(plot_height=200, sizing_mode='scale_width')
    plot.line('x', 'y', source=source, line_width=4)
    plot.xaxis.axis_label = "Iterations over time"

    script, div = components(plot, CDN)
    return script, div

def make_demo_plot():
    source = AjaxDataSource(data_url=resolve_url('demo_data'),
                            polling_interval=2000, mode='replace')

    source.data = dict(x=[], y=[])

    plot = figure(plot_height=200, sizing_mode='scale_width')
    plot.line('x', 'y', source=source, line_width=4)

    script, div = components(plot, CDN)
    return script, div

@csrf_exempt
def data_demo(request):
    obs = net.get_observable()["Rmse"]
    data = {
        "x": obs[0],
        "y": obs[1]
    }
    return JsonResponse(data)

@csrf_exempt
def demo(request):
    global x
    global y
    x = 0
    y = 0
    plots = []
    data_path = os.path.join(settings.BASE_DIR, "users/Demo/demo")
    plots.append({'plot': make_demo_plot(), 'name':"spectral_radius", 'verbose_name':"Rmse"})
    net.add_observable("Rmse", 10)

    net.add_task(data_path, 0, 100, "Train")
    net.add_task(data_path, 100, 120, "Test")
    net.add_task(data_path, 1, 23, "Train")
    net.add_task(data_path, 0, 80, "Test")
    net.add_task(data_path, 20, 115, "Train")
    net.add_task(data_path, 49, 130, "Test")
    net.add_task(data_path, 90, 143, "Train")
    net.add_task(data_path, 42, 99, "Test")
    net.start()
    return render(request, "ARNN/demo.html", {"plots": plots})
