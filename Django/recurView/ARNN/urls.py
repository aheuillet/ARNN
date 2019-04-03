from django.urls import path
from django.conf.urls import url, include
from ARNN import networkcontrol, templates_control, corpus_control
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView, LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from . import views
from . import demo

urlpatterns = [
    path('', login_required(csrf_exempt(views.index)), name='index'),
    #path('test/', BaseControl.as_view(), name='test'),
    path('logout/', auth_views.LogoutView.as_view(template_name='home.html')),
    path('corpus/create', corpus_control.create, name='corpus_create'),
    path('corpus/generate', corpus_control.generate, name='corpus_generate'),
    path('corpus/list', corpus_control.liste, name='corpus_list'),
    path('corpus/download/<int:pk>/', corpus_control.download, name='corpus_download'),
    path('corpus/delete/<int:pk>/', corpus_control.delete, name='corpus_delete'),
    path('corpus/get_size/<int:pk>/', corpus_control.corpus_size, name='corpus_size'),
    path('corpus/get_dims/<int:pk>/', corpus_control.get_dims, name='get_dims'),
    path('template/create', templates_control.create, name='template_create'),
    path('template/list', templates_control.list, name='template_list'),
    path('template/delete/<int:pk>/', templates_control.delete, name='template_delete'),
    path('template/download/<int:pk>/', templates_control.download, name='template_download'),
    path('network/create', networkcontrol.create, name='network_create'),
    path('network/list', networkcontrol.list_net, name='network_list'),
    path('network/delete/<int:pk>/', networkcontrol.delete, name='network_delete'),
    path('network/download/<int:pk>/', networkcontrol.download, name='network_download'),
    path('network/autosaved/<int:pk>/', networkcontrol.get_network_saved, name='get_network_saved'),
    path('network/get_dims/<int:pk>/', networkcontrol.get_dims, name='get_dims'),
    path('login', auth_views.LoginView.as_view(template_name='registration/login.html')),
    path('reset-password/', PasswordResetView.as_view(), name='reset_password'),
    path('reset-password/done/', PasswordResetDoneView.as_view(), name='reset_password_done'),
    path('reset-password/confirm/', PasswordResetConfirmView.as_view(), name='reset_password_confirm'),
    path('reset-password/complete/', PasswordResetCompleteView.as_view(), name='reset_password_complete'),
    path('control/', csrf_exempt(networkcontrol.NetworkRunControl.as_view()), name='control'),
    path('demo/', demo.demo, name='demo'),
    path('demo/data/', demo.data_demo, name='demo_data'),
    url('^', include('django.contrib.auth.urls'))
]
