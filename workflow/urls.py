from django.conf.urls import patterns, url

from workflow import views
 
urlpatterns= patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^workflowlanguage.js', views.workflow_language, name='workflow_language')
)
