from django.conf.urls import patterns, url

from sipcreator import views
import earkcore

from django.views.decorators.csrf import csrf_exempt
 
urlpatterns= patterns('',

    url(r'^$', views.InformationPackageList.as_view(), name='index'),

    url(r'^index$', views.InformationPackageList.as_view(), name='index'),

    url(r'^start$', views.start, name='start'),

    url(r'^detail/(?P<pk>\d+)/$', views.sip_detail, name='ip_detail'),

    url(r'^detail/(?P<pk>\d+)/(?P<rep>[A-Za-z0-9-_]{4,200})/$', views.sip_detail_rep, name='sip_detail_rep'),

    url(r'^add_file/(?P<uuid>[a-z0-9-]{36,36})/(?P<subfolder>[a-z/\._]{1,50})', views.add_file, name='add_file'),

    url(r'^initialize/(?P<packagename>.*)', views.initialize, name='initialize'),

    url(r'^sipcreation/(?P<pk>\d+)/$', views.SIPCreationDetail.as_view(), name='sipcreation'),

    url(r'^working_area/(?P<section>[a-z0-9]{1,20})/(?P<uuid>[a-z0-9\-]{36,36})/$', earkcore.views.working_area, name='working_area'),

    url(r'^help_processing_status$', views.HelpProcessingStatus.as_view(), name='help_processing_status'),



    url(r'^ip_detail_table$', views.ip_detail_table, name='ip_detail_table'),

    url(r'^add_representation/(?P<pk>\d+)/$', views.add_representation, name='add_representation'),

    url(r'^delete/(?P<pk>\d+)/$', views.delete, name='delete'),

    url(r'^update_parent_identifier/(?P<pk>\d+)/$', views.update_parent_identifier, name='update_parent_identifier'),
)
