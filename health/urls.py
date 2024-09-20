"""health check url configuration
"""
from django.urls import re_path, path
from django.contrib import admin
import health.views

app_name = 'health'

urlpatterns = [
    re_path(r'^$', health.views.index, name='none'),
    re_path(r'^ready$', health.views.ready, name='ready'),
    re_path(r'^index$', health.views.index, name='index'),
    re_path(r'^addperson$', health.views.addperson, name='addperson'),
    re_path(r'^testmq$', health.views.testmq, name='testmq'),
    re_path(r'^testmq_publish$', health.views.testmq_publish, name='testmq_publish'),
    re_path(r'^testmq_consume$', health.views.testmq_consume, name='testmq_consume'),
    re_path(r'^publish_message_action$', health.views.publish_message_action, name='publish_message_action'),
    re_path(r'^consume_message_action$', health.views.consume_message_action, name='consume_message_action'),
    re_path(r'^testtask$', health.views.testtask, name='testtask'),
]