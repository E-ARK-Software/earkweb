from django.conf.urls import patterns, url

from sipcreator import views

from django.views.decorators.csrf import csrf_exempt
 
urlpatterns= patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^index$', views.index, name='index'),
    url(r'^add_file/(?P<uuid>[a-z0-9-]{36,36})/(?P<subfolder>[a-z/\._]{1,50})/(?P<datafolder>[a-z]{1,50})', views.add_file, name='add_file'),
    url(r'^initialize/(?P<packagename>.*)', views.initialize, name='initialize'),
    url(r'^sipcreation$', views.sipcreation, name='sipcreation'),
    url(r'^working_area/(?P<uuid>[a-z0-9-]{36,36})/$', views.working_area, name='working_area'),
    url(r'^delete/(?P<uuid>[a-z0-9-]{36,36})/$', views.delete, name='delete'),
)
