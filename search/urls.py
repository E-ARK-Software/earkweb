from django.conf.urls import patterns, url

from search import views
 
urlpatterns= patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^start$', views.start, name='start'),
    url(r'^packsel$', views.packsel, name='packsel'),
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
)
