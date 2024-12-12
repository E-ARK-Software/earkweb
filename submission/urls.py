from django.urls import re_path, path
import submission.views
import earkweb.views

app_name = 'submission'

urlpatterns = [
    re_path(r'^$', submission.views.informationpackages_overview, name='default'),
    re_path(r'^index', submission.views.index, name='index'),
    re_path(r'^overview', submission.views.informationpackages_overview, name='overview'),
    re_path(r'^start$', submission.views.start, name='start'),
    re_path(r'^upload$', submission.views.upload, name='upload'),
    re_path(r'^upload-packaged-sip$', submission.views.upload_packaged_sip, name='upload-packaged-sip'),
    re_path(r'^ip_upload$', submission.views.ip_upload, name='ip_upload'),
    re_path(r'^upload_step1/(?P<pk>\d+)/?', submission.views.upload_step1, name='upload_step1'),
    re_path(r'^upload_step2/(?P<pk>\d+)/?', submission.views.upload_step2, name='upload_step2'),
    re_path(r'^upload_step3/(?P<pk>\d+)/?', submission.views.upload_step3, name='upload_step3'),
    re_path(r'^upload_step4/(?P<pk>\d+)/?', submission.views.upload_step4, name='upload_step4'),
    re_path(r'^upload_step5/(?P<pk>\d+)/?', submission.views.upload_step5, name='upload_step5'),
    re_path(r'^updatedistrmd', submission.views.updatedistrmd, name='updatedistrmd'),
    re_path(r'^upload_step5/(?P<pk>\d+)/(?P<rep>[A-Za-z0-9-_]{4,200})/$', submission.views.upload_step5_rep, name='upload_step5_rep'),
    re_path(r'^ips_table$', submission.views.informationpackages_overview, name='ips_table'),
    re_path(r'^ip_creation_process/(?P<pk>\d+)/$', submission.views.ip_creation_process, name='ip_creation_process'),
    re_path(r'^upload_finalize/(?P<pk>\d+)/$', submission.views.upload_finalize, name='upload_finalize'),
    re_path(r'^detail/(?P<pk>\d+)/$', submission.views.InformationPackageDetail.as_view(), name='ip_detail'),
    re_path(r'^detail/(?P<pk>\d+)/(?P<rep>[A-Za-z0-9-_]{4,200})/$', submission.views.sip_detail_rep, name='sip_detail_rep'),
    re_path(r'^add_file/(?P<uid>[a-z0-9-]{36,36})/(?P<subfolder>[a-z/\._]{1,50})$', submission.views.add_file, name='add_file'),
    re_path(r'^initialize/$', submission.views.initialize, name='initialize'),
    re_path(r'^ips/(?P<pk>\d+)/startingest$', submission.views.StartIngestDetail.as_view(), name='startingest'),
    re_path(r'^working_area/(?P<section>[a-z0-9]{1,20})/(?P<uid>[a-z0-9\-]{36,36})/$', earkweb.views.working_area2, name='working_area'),
    re_path(r'^ip_detail_table$', submission.views.ip_detail_table, name='ip_detail_table'),
    re_path(r'^add_representation/(?P<pk>\d+)/$', submission.views.add_representation, name='add_representation'),
    re_path(r'^del_representation/(?P<uid>[a-z0-9-]{36,40})/(?P<representation_id>[a-z0-9-]{36,36})/$', submission.views.del_representation, name='del_representation'),
    re_path(r'^delete/(?P<pk>\d+)/$', submission.views.delete, name='delete'),
    re_path(r'^uid/(?P<pk>\d+)/$', submission.views.ip_by_primary_key, name='sip_uid'),
    re_path(r'^ins_file/(?P<uid>[a-z0-9-]{36,36})/(?P<subfolder>[a-z/\._]{1,50})$', submission.views.ins_file, name='ins_file'),
    re_path(r'^batch$', submission.views.SipCreationBatchView.as_view(), name='batch'),
    #re_path(r'^submit_sipcreation_batch/(?P<uid>[0-9a-zA-Z_\-\./ ]{3,500})/$', views.submit_sipcreation_batch, name='submit_sipcreation_batch'),
    re_path(r'^fileresource/(?P<item>[a-z0-9\-:+]{36,50})/(?P<ip_sub_file_path>.*)/$', submission.views.fileresource, name='fileview'),
    re_path(r'^receptionresource/(?P<ip_sub_file_path>.*)/$', submission.views.receptionresource, name='receptionresource'),
    re_path(r'^reception-task-status/(?P<task_id>.+)/$', submission.views.reception_task_status, name='reception-task-status'), 
    re_path(r'^apply_task', submission.views.apply_task, name='apply_task'),
    re_path(r'^poll_state$', submission.views.poll_state, name='poll_state'),
    re_path(r'^get_directory_json$', earkweb.views.get_directory_json, name='get_directory_json'),
    re_path(r'^get_autocomplete/$', submission.views.get_autocomplete, name='get_autocomplete'),
    re_path(r'^get_autocomplete_tags/$', submission.views.get_autocomplete_tags, name='get_autocomplete_tags'),

]
