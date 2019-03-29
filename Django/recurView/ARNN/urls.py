from django.urls import path
from django.conf.urls import url, include
from ARNN import networkcontrol, templates_control, corpus_control
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView, LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from . import views
from . import bokeh

urlpatterns = [
    path('', login_required(csrf_exempt(views.index)), name='index'),
    #path('test/', BaseControl.as_view(), name='test'),
    path('logout/', auth_views.LogoutView.as_view(template_name='home.html')),
    path('corpus/create', corpus_control.create, name='corpus_create'),
    path('corpus/list', corpus_control.liste, name='corpus_list'),
    path('corpus/edit/<int:pk>/', corpus_control.edit, name='corpus_edit'),
    path('corpus/delete/<int:pk>/', corpus_control.delete, name='corpus_delete'),
    path('template/create', templates_control.create, name='template_create'),
    path('template/list', templates_control.list, name='template_list'),
    path('template/edit/<int:pk>/', templates_control.edit, name='template_edit'),
    path('template/delete/<int:pk>/', templates_control.delete, name='template_delete'),
    path('network/create', networkcontrol.create, name='network_create'),
    path('network/list', networkcontrol.list, name='network_list'),
    path('network/edit/<int:pk>/', networkcontrol.edit, name='network_edit'),
    path('network/delete/<int:pk>/', networkcontrol.delete, name='network_delete'),
    path('login', auth_views.LoginView.as_view(template_name='registration/login.html')),
    path('reset-password/', PasswordResetView.as_view(), name='reset_password'),
    path('reset-password/done/', PasswordResetDoneView.as_view(), name='reset_password_done'),
    path('reset-password/confirm/', PasswordResetConfirmView.as_view(), name='reset_password_confirm'),
    path('reset-password/complete/', PasswordResetCompleteView.as_view(), name='reset_password_complete'),
    path('control/', csrf_exempt(networkcontrol.NetworkRunControl.as_view()), name='control'),
    path('demo/', bokeh.demo, name='demo'),
    path('demo/data/', bokeh.data_demo, name='demo_data'),
    url('^', include('django.contrib.auth.urls'))
]
