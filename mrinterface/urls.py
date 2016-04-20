from django.conf.urls import patterns, url

import earkcore

from mrinterface import views

urlpatterns = patterns('',

    url(r'^start$', views.start, name='start'),

)
