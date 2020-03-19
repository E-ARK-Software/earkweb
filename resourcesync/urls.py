#!/usr/bin/env python
# coding=UTF-8
from django.conf.urls import url

import resourcesync.views

app_name = 'resourcesync'

urlpatterns = [
    url(r'^$', resourcesync.views.index, name='index'),
    url(r'^changelist.xml', resourcesync.views.changelist, name='changelist'),
    #url(r'^resources$', resourcesync.views.changelist, name='resources'),
    url(r'^resources/(?P<identifier>[0-9a-zA-Z-_/\.\:]{3,200})/$', resourcesync.views.resource, name='resource'),
]
