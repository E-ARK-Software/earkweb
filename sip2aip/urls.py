from django.conf.urls import patterns, url

from sip2aip import views

from earkcore.views import InformationPackageDetailView

urlpatterns= patterns('',

    url(r'^$', views.InformationPackageList.as_view(),name='reception'),

    url(r'^detail/(?P<pk>\d+)/$', views.InformationPackageDetail.as_view(), name='ip_detail'),

    url(r'^progress$', views.progress, name='progress'),

    url(r'^do_task$', views.do_task, name='do_task'),

    url(r'^poll_state$', views.poll_state, name='poll_state'),

)
