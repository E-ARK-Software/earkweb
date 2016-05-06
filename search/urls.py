from django.conf.urls import patterns, url
from django.views.generic import RedirectView
import earkcore.views
from search import views
 
urlpatterns= patterns('',
    url(r'^$', RedirectView.as_view(url='selection'), name='index'),
    url(r'^selection$', RedirectView.as_view(url='selection/default'), name='selection'),
    #url(r'^search$)', views.index, name='search'),
    url(r'^selection/(?P<procname>.*)', views.index, name='search'),
    url(r'^start$', views.start, name='start'),
    url(r'^packsel$', views.packsel, name='packsel'),
    url(r'^help_processing_status$', views.HelpProcessingStatus.as_view(), name='help_processing_status'),
    url(r'^remproc$', views.remproc, name='remproc'),
    url(r'^remaip$', views.remaip, name='rempaip'),
    url(r'^localrepo$', views.localrepo, name='localrepo'),
    url(r'^demosearch$', views.demosearch, name='demosearch'),
    url(r'^demosearch/govdocs$', views.demosearch_govdocs, name='demosearch_govdocs'),
    url(r'^demosearch/news$', views.demosearch_news, name='demosearch_news'),
    url(r'^demosearch/package$', views.demosearch_package, name='demosearch_package$'),
    url(r'^search_form.*', views.search_form, name='search_form'),
    url(r'^toggle_select_package.*', views.toggle_select_package, name='toggle_select_package'), 
    #url(r'^$', 'search_form', name="search_form"),
    url(r'^filecontent/(?P<lily_id>.*)', views.get_file_content, name='filecontent'),
    url(r'^create_dip$', views.create_dip, name='create_dip'),
    url(r'^dip/([^/]+)$', views.dip, name='dip'),
    url(r'^dip/([^/]+)/acquire_aips$', views.acquire_aips, name='acquire_aips'),
    url(r'^dip/([^/]+)/attach_aip$', views.attach_aip, name='attach_aip'),
    url(r'^dip/([^/]+)/aip/([^/]+)$', views.aip, name='aip'),
    url(r'^dip_detail_table$', views.dip_detail_table, name='dip_detail_table'),
    url(r'^working_area/(?P<section>[a-z0-9]{1,20})/(?P<uuid>[a-z0-9-]{36,36})/$', earkcore.views.working_area, name='working_area'),
    url(r'^submit_order/', views.submit_order, name='submit_order'),
    url(r'^order_status/', views.order_status, name='order_status'),
)
