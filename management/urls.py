from django.urls import re_path, path
import management.views
import earkweb.views

from config.configuration import identifier_pattern

app_name = 'management'

urlpatterns = [
    re_path(r'^$', management.views.informationpackages_overview, name='overview'),
    re_path(r'^overview$', management.views.informationpackages_overview, name='overview'),
    re_path(r'^render_network$', management.views.render_network, name='render_network'),
    re_path(r'^ips_table$', management.views.informationpackages_overview, name='ips_table'),
    re_path(r'^detail/(?P<pk>\d+)/$', management.views.InformationPackageDetail.as_view(), name='resubmit'),
    re_path(r'^modify/(?P<pk>\d+)/$', management.views.sip_detail, name='ip_detail'),
    re_path(r'^delete/(?P<pk>\d+)/$', management.views.delete, name='delete'),
    re_path(r'^ip_detail_table$', management.views.ip_detail_table, name='ip_detail_table'),
    re_path(r'^working_area/(?P<section>[a-z0-9]{1,20})/(?P<uid>[a-z0-9\-]{36,36})/$', earkweb.views.working_area2, name='working_area'),
    re_path(r'^storage_area/(?P<section>[a-z0-9]{1,20})/(?P<identifier>%s)/$' % identifier_pattern, earkweb.views.storage_area, name='storage_area'),
    re_path(r'^get_directory_json$', earkweb.views.get_directory_json, name='get_directory_json'),
]
