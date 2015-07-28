from django.conf.urls import patterns, url

from sip2aip import views

from earkcore.views import InformationPackageDetailView

urlpatterns= patterns('',
    url(r'^$', views.index, name='index'),

    url(r'^reception/$', views.InformationPackageList.as_view(),name='reception'),

)
