from django.conf.urls import patterns, url

from search import views

urlpatterns= patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^article/(?P<article_id>.*)', views.article, name='article'),
    url(r'^search_form.*', views.search_form, name='search_form'),
    url(r'^toggle_select_package.*', views.toggle_select_package, name='toggle_select_package'), 
    #url(r'^$', 'search_form', name="search_form"),
)