from django.conf.urls import url

import management.views
import earkweb.views

app_name = 'management'

urlpatterns = [
    url(r'^$', management.views.informationpackages_overview, name='overview'),
    url(r'^overview$', management.views.informationpackages_overview, name='overview'),
    url(r'^render_network$', management.views.render_network, name='render_network'),
    url(r'^ips_table$', management.views.informationpackages_overview, name='ips_table'),
    url(r'^detail/(?P<pk>\d+)/$', management.views.InformationPackageDetail.as_view(), name='resubmit'),
    url(r'^modify/(?P<pk>\d+)/$', management.views.sip_detail, name='ip_detail'),
    url(r'^delete/(?P<pk>\d+)/$', management.views.delete, name='delete'),
    url(r'^ip_detail_table$', management.views.ip_detail_table, name='ip_detail_table'),
    url(r'^checkout/(?P<identifier>[a-z0-9\-:]{40,50})/$', management.views.checkout, name='checkout'),
    url(r'^working_area/(?P<section>[a-z0-9]{1,20})/(?P<uid>[a-z0-9\-]{36,36})/$', earkweb.views.working_area2, name='working_area'),
    url(r'^storage_area/(?P<section>[a-z0-9]{1,20})/(?P<identifier>[a-z0-9\-:]{40,50})/$', earkweb.views.storage_area, name='storage_area'),
    url(r'^get_directory_json$', earkweb.views.get_directory_json, name='get_directory_json'),
]
