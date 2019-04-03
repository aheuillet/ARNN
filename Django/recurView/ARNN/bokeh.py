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

def make_ajax_plot(observable, dim, network_ID):
    """This function is used to create a new Bokeh instance to send to the view.

        Inputs:
        -observable: a string containing the name of the observable to poll for.
        -network_ID: an int referring to the network whose observable need to be fetched.
    """
    source = AjaxDataSource(method='GET', data_url=resolve_url('control') + "?method=get_observable&observable=" + str(observable) + "&network_ID=" + str(network_ID),
                            polling_interval=3000, mode='replace')
    source.data = dict(x=[])
    for i in range(dim):
        source.data["y"+str(i)]=[]

    plot = figure(plot_height=200, sizing_mode='scale_width')
    span = int(256*256*256/(dim+1)) + 1
    a = (int(span/(255*255)),int(span/(255))%255, span%255)
    print(a)
    for i in range(dim):
        plot.line('x', 'y'+str(i), source=source, line_width=2, line_color="#%02x%02x%02x" % (int(i*span/(255*255))+1,int(i*span/(255))%(255)+1, i*span%255+1))
    
    plot.xaxis.axis_label = "Iterations over time"

    script, div = components(plot, CDN)
    return script, div
