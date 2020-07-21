from django.views.generic import RedirectView

from django.conf.urls import url
from django.contrib import admin

import administration.urls
import health.urls

from earkweb import views
from earkweb.views import ActivateLanguageView
from config.configuration import log_current_configuration

from django.urls import path, include

app_name = 'earkweb'

urlpatterns = [
    url(r'^language/activate/(?P<language_code>[DE|de|EN|en]{2,2})/?', ActivateLanguageView.as_view(), name='activate_language'),
    url(r'^health/', include(health.urls)),
    url(r'^administration/', include(administration.urls)),
    url(r'^$', RedirectView.as_view(url='home')),
    url(r'^home', views.home, name='home'),
    url(r'^earkweb/version', views.version, name='version'),
    url(r'^access/', include('access.urls')),
    url(r'^submission/', include('submission.urls')),
    url(r'^management/', include('management.urls')),
    url(r'^admin', admin.site.urls),
    url(r'^api/?', include('api.urls')),
    url(r'^rs/?', include('resourcesync.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    url(r'^check_folder_exists/(?P<folder>[0-0a-zA-Z_/]{3,200})/$', views.check_folder_exists, name='check_folder_exists'),
    url(r'^check_submission_exists/(?P<package_name>[0-9a-zA-Z-_/\.]{3,200})/$', views.check_submission_exists, name='check_submission_exists'),
    url(r'^check_identifier_exists/(?P<identifier>[0-9a-zA-Z-_/\.\:]{3,200})/$', views.check_identifier_exists, name='check_identifier_exists'),
    url(r'^read-file/(?P<ip_sub_file_path>.*)/$', views.read_file, name='read-file'),
    url(r'^get_directory_json/$', views.get_directory_json, name='get_directory_json'),
    url(r'^get_storage_directory_json$', views.get_storage_directory_json, name='get_storage_directory_json'),
    url(r'^poll_state/$', views.poll_state, name='poll_state'),
    url(r'^solrif/(?P<core>[0-9a-zA-Z-]{3,200})/(?P<operation>[0-9a-zA-Z-]{3,200})/$', views.solrif, name='solrif'),
]

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='earkweb/')),
    url(r'^earkweb/', include(urlpatterns)),
]


# print configuration parameters at application startup
log_current_configuration()