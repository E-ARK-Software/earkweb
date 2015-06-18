from django.conf.urls import patterns, url

from workflow import views
 
urlpatterns= patterns('',
    url(r'^$', views.index, name='index')
)
