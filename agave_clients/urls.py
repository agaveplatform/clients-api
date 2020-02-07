from django.conf.urls import url

from django.contrib import admin
from rest_framework.urlpatterns import format_suffix_patterns

from agave_clients.service import views

admin.autodiscover()

urlpatterns = [

    # rest API:
    url(r'clients/v2/(?P<client_name>.*[^/])/subscriptions/$', views.ClientSubscriptions.as_view(),
        name='client_subscriptions'),
    url(r'clients/v2/(?P<client_name>.*[^/])/subscriptions$', views.ClientSubscriptions.as_view()),

    url(r'clients/v2/(?P<client_name>.*[^/])/$', views.ClientDetails.as_view()),
    url(r'clients/v2/(?P<client_name>.*[^/])$', views.ClientDetails.as_view(), name='client_details'),

    url(r'clients/v2/', views.Clients.as_view(), name='clients'),
    url(r'clients/v2', views.Clients.as_view()),

]

urlpatterns = format_suffix_patterns(urlpatterns)