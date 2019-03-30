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
