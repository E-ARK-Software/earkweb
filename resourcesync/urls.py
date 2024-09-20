#!/usr/bin/env python
# coding=UTF-8
from django.urls import re_path, path
import resourcesync.views

app_name = 'resourcesync'

urlpatterns = [
    re_path(r'^$', resourcesync.views.index, name='index'),
    re_path(r'^changelist.xml', resourcesync.views.changelist, name='changelist'),
    #re_path(r'^resources$', resourcesync.views.changelist, name='resources'),
    re_path(r'^resources/(?P<identifier>[0-9a-zA-Z-_/\.\:]{3,200})/$', resourcesync.views.resource, name='resource'),
]
