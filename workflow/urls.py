from django.conf.urls import patterns, url

from workflow import views

from django.views.decorators.csrf import csrf_exempt
 
urlpatterns= patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^workflowlanguage.js', views.workflow_language, name='workflow_language'),
    url(r'^backend', csrf_exempt(views.backend), name='backend')
)
