from django.conf.urls import patterns, url

from earkcore import views

urlpatterns= patterns('',

    url(r'^check_folder_exists/(?P<folder>[0-0a-zA-Z_/]{3,200})/$', views.check_folder_exists, name='check_folder_exists'),
    url(r'^check_submission_exists/(?P<packagename>[0-9a-zA-Z_/\.]{3,200})/$', views.check_submission_exists, name='check_submission_exists'),
    url(r'^check_identifier_exists/(?P<identifier>[0-9a-zA-Z-_/\.]{3,200})/$', views.check_identifier_exists, name='check_identifier_exists'),
    url(r'^save_parent_identifier/(?P<uuid>[0-9a-zA-Z-_/\.]{3,200})/$', views.save_parent_identifier, name='save_parent_identifier'),
    url(r'^read_ipfc/(?P<ip_sub_file_path>[0-9a-zA-Z_\-/\. ]{3,500})/$', views.read_ipfc, name='read_ipfc'),
    url(r'^get_directory_json$', views.get_directory_json, name='get_directory_json'),

)
