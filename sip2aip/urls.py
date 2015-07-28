from django.conf.urls import patterns, url

from sip2aip import views

urlpatterns= patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^reception$', views.reception, name='reception'),
)
