from django.conf.urls import patterns, url

import earkcore

from datamining import views

urlpatterns = patterns('',

    url(r'^start$', views.start, name='start'),

    url(r'^celery_nlp_new_collection$', views.celery_nlp_new_collection, name='celery_nlp_new_collection'),

    url(r'^celery_nlp_existing_collection$', views.celery_nlp_existing_collection, name='celery_nlp_existing_collection'),

)
