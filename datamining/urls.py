from django.conf.urls import patterns, url

import earkcore

from datamining import views

urlpatterns = patterns('',

    url(r'^start$', views.start, name='start'),

    url(r'^start$', views.celery_nlp, name='celery_nlp'),

)
