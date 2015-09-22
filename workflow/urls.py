from django.conf.urls import patterns, url

from workflow import views
import earkcore.views

from django.views.decorators.csrf import csrf_exempt
 
urlpatterns= patterns('',
    url(r'^$', views.index, name='index'),

    url(r'^workflowlanguage.js', views.workflow_language, name='workflow_language'),

    url(r'^backend', csrf_exempt(views.backend), name='backend'),

    url(r'^execution$', views.execution, name='execution'),

    url(r'^apply_task', views.apply_task, name='apply_task'),

    url(r'^apply_workflow', views.apply_workflow, name='apply_workflow'),

    url(r'^poll_state$', views.poll_state, name='poll_state'),

    url(r'^get_directory_json$', earkcore.views.get_directory_json, name='get_directory_json'),
)
