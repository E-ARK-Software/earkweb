from django.conf.urls import url

import submission.views
import earkweb.views

app_name = 'submission'

urlpatterns = [
    url(r'^$', submission.views.informationpackages_overview, name='default'),
    url(r'^index', submission.views.index, name='index'),
    url(r'^overview', submission.views.informationpackages_overview, name='overview'),
    url(r'^start$', submission.views.start, name='start'),
    url(r'^upload$', submission.views.upload, name='upload'),
    url(r'^upload_step1/(?P<pk>\d+)/?', submission.views.upload_step1, name='upload_step1'),
    url(r'^upload_step2/(?P<pk>\d+)/?', submission.views.upload_step2, name='upload_step2'),
    url(r'^upload_step4/(?P<pk>\d+)/?', submission.views.upload_step4, name='upload_step4'),
    url(r'^updatedistrmd', submission.views.updatedistrmd, name='updatedistrmd'),
    url(r'^upload_step4/(?P<pk>\d+)/(?P<rep>[A-Za-z0-9-_]{4,200})/$', submission.views.upload_step4_rep, name='upload_step4_rep'),
    url(r'^ips_table$', submission.views.informationpackages_overview, name='ips_table'),
    url(r'^ip_creation_process/(?P<pk>\d+)/$', submission.views.ip_creation_process, name='ip_creation_process'),
    url(r'^upload_finalize/(?P<pk>\d+)/$', submission.views.upload_finalize, name='upload_finalize'),
    url(r'^detail/(?P<pk>\d+)/$', submission.views.InformationPackageDetail.as_view(), name='ip_detail'),
    url(r'^detail/(?P<pk>\d+)/(?P<rep>[A-Za-z0-9-_]{4,200})/$', submission.views.sip_detail_rep, name='sip_detail_rep'),
    url(r'^add_file/(?P<uid>[a-z0-9-]{36,36})/(?P<subfolder>[a-z/\._]{1,50})$', submission.views.add_file, name='add_file'),
    url(r'^initialize/$', submission.views.initialize, name='initialize'),
    url(r'^ips/(?P<pk>\d+)/startingest$', submission.views.StartIngestDetail.as_view(), name='startingest'),
    url(r'^working_area/(?P<section>[a-z0-9]{1,20})/(?P<uid>[a-z0-9\-]{36,36})/$', earkweb.views.working_area2, name='working_area'),
    url(r'^ip_detail_table$', submission.views.ip_detail_table, name='ip_detail_table'),
    url(r'^add_representation/(?P<pk>\d+)/$', submission.views.add_representation, name='add_representation'),
    url(r'^del_representation/(?P<uid>[a-z0-9-]{36,40})/(?P<representation_id>[a-z0-9-]{36,36})/$', submission.views.del_representation, name='del_representation'),
    url(r'^delete/(?P<pk>\d+)/$', submission.views.delete, name='delete'),
    url(r'^uid/(?P<pk>\d+)/$', submission.views.ip_by_primary_key, name='sip_uid'),
    url(r'^ins_file/(?P<uid>[a-z0-9-]{36,36})/(?P<subfolder>[a-z/\._]{1,50})$', submission.views.ins_file, name='ins_file'),

    url(r'^batch$', submission.views.SipCreationBatchView.as_view(), name='batch'),
    #url(r'^submit_sipcreation_batch/(?P<uid>[0-9a-zA-Z_\-\./ ]{3,500})/$', views.submit_sipcreation_batch, name='submit_sipcreation_batch'),

    url(r'^fileresource/(?P<item>[a-z0-9\-:+]{36,50})/(?P<ip_sub_file_path>.*)/$', submission.views.fileresource, name='fileview'),

    url(r'^apply_task', submission.views.apply_task, name='apply_task'),
    url(r'^poll_state$', submission.views.poll_state, name='poll_state'),
    url(r'^get_directory_json$', earkweb.views.get_directory_json, name='get_directory_json'),

    url(r'^get_autocomplete/$', submission.views.get_autocomplete, name='get_autocomplete'),
    url(r'^get_autocomplete_tags/$', submission.views.get_autocomplete_tags, name='get_autocomplete_tags'),

]
