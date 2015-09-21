from django.conf.urls import patterns, url

from earkcore import views

urlpatterns= patterns('',

    url(r'^check_folder_exists/(?P<folder>[0-0a-zA-Z_/]{3,200})/$', views.check_folder_exists, name='check_folder_exists'),
    url(r'^check_submission_exists/(?P<packagename>[0-9a-zA-Z_/\.]{3,200})/$', views.check_submission_exists, name='check_submission_exists'),

)
