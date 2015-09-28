from django.conf.urls import patterns, url

from sipcreator import views
import earkcore

from django.views.decorators.csrf import csrf_exempt
 
urlpatterns= patterns('',

    url(r'^$', views.InformationPackageList.as_view(), name='index'),

    url(r'^index$', views.InformationPackageList.as_view(), name='index'),

    url(r'^start$', views.start, name='start'),

    url(r'^detail/(?P<pk>\d+)/$', views.InformationPackageDetail.as_view(), name='ip_detail'),

    url(r'^add_file/(?P<uuid>[a-z0-9-]{36,36})/(?P<subfolder>[a-z/\._]{1,50})/(?P<datafolder>[a-z]{1,50})', views.add_file, name='add_file'),

    url(r'^initialize/(?P<packagename>.*)', views.initialize, name='initialize'),

    url(r'^sipcreation/(?P<pk>\d+)/$', views.SIPCreationDetail.as_view(), name='sipcreation'),

    url(r'^working_area/(?P<section>[a-z0-9]{1,20})/(?P<uuid>[a-z0-9\-]{36,36})/$', earkcore.views.working_area, name='working_area'),

    url(r'^help_processing_status$', views.help_processing_status, name='help_processing_status'),

    url(r'^delete/(?P<pk>\d+)/$', views.delete, name='delete'),
)
