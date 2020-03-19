"""health check url configuration
"""
from django.conf.urls import include, url
from django.contrib import admin
import health.views

app_name = 'health'

urlpatterns = [
    url(r'^$', health.views.index, name='none'),
    url(r'^ready$', health.views.ready, name='ready'),
    url(r'^index$', health.views.index, name='index'),
    url(r'^addperson$', health.views.addperson, name='addperson'),
    url(r'^testmq$', health.views.testmq, name='testmq'),
    url(r'^testmq_publish$', health.views.testmq_publish, name='testmq_publish'),
    url(r'^testmq_consume$', health.views.testmq_consume, name='testmq_consume'),
    url(r'^publish_message_action$', health.views.publish_message_action, name='publish_message_action'),
    url(r'^consume_message_action$', health.views.consume_message_action, name='consume_message_action'),
    url(r'^testtask$', health.views.testtask, name='testtask'),
]