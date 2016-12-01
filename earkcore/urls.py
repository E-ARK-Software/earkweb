from django.conf.urls import patterns, url

from earkcore import views

urlpatterns= patterns('',

    url(r'^ipview/(?P<identifier>[0-9a-zA-Z-_/\.\:]{3,200})/$', views.ipview, name='ipview'),
    url(r'^check_folder_exists/(?P<folder>[0-0a-zA-Z_/]{3,200})/$', views.check_folder_exists, name='check_folder_exists'),
    url(r'^check_submission_exists/(?P<packagename>[0-9a-zA-Z-_/\.]{3,200})/$', views.check_submission_exists, name='check_submission_exists'),
    url(r'^check_identifier_exists/(?P<identifier>[0-9a-zA-Z-_/\.\:]{3,200})/$', views.check_identifier_exists, name='check_identifier_exists'),
    url(r'^save_parent_identifier/(?P<uuid>[0-9a-zA-Z-_/\.]{3,200})/$', views.save_parent_identifier, name='save_parent_identifier'),
    url(ur'^read_ipfc/(?P<ip_sub_file_path>.*)/$', views.read_ipfc, name='read_ipfc'),
    # access url pattern: <repo-access-endpoint>/<identifier>/<mime-type>/<package-entry>/
    url(r'^access_aip_item/(?P<identifier>[0-9a-zA-Z_\-\. \:]{3,500})/(?P<mime>([0-9a-zA-Z_\-\. ]{2,20}/[0-9a-zA-Z_\-\.+ ]{2,100}))/(?P<entry>[0-9a-zA-Z_\-/\. \:]{3,500})/$', views.access_aip_item, name='access_aip_item'),
    url(r'^get_directory_json$', views.get_directory_json, name='get_directory_json'),
    url(r'^get_directory_json_remote/(?P<dir>[0-9a-zA-Z_\-\./ ]{3,500})/$', views.get_directory_json_remote, name='get_directory_json_remote'),
    url(r'^poll_state/$', views.poll_state, name='poll_state'),
    url(r'^reindex_aip_storage/$', views.reindex_aip_storage, name='reindex_aip_storage'),
    url(r'^xmleditor/(?P<uuid>[0-9a-zA-Z-]{3,200})/(?P<ip_xml_file_path>[0-9a-zA-Z_\-/\. ]{3,500})/$', views.xmleditor, name='xmleditor'),
    url(r'^savexml/(?P<uuid>[0-9a-zA-Z-]{3,200})/(?P<ip_xml_file_path>[0-9a-zA-Z_\-/\. ]{3,500})/$', views.savexml, name='savexml'),
    url(r'^set_proc_state_valid/(?P<uuid>[0-9a-zA-Z-]{3,200})/$', views.set_proc_state_valid, name='setprocvalid'),
    url(r'^solrif/(?P<core>[0-9a-zA-Z-]{3,200})/(?P<operation>[0-9a-zA-Z-]{3,200})/$', views.solrif, name='solrif'),
    url(r'^solrinterface/(?P<query>.*)/$', views.solrinterface, name='solrinterface'),
    url(r'^start_hdfs_batch_upload/$', views.start_hdfs_batch_upload, name='start_hdfs_batch_upload'),
    url(r'^index_local_storage_ip$', views.index_local_storage_ip, name='index_local_storage_ip'),

)
