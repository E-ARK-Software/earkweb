from django.views.generic import RedirectView

from django.urls import re_path, path
from django.contrib import admin

import administration.urls
import health.urls

from earkweb import views
from earkweb.views import ActivateLanguageView
from config.configuration import log_current_configuration

from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

app_name = 'earkweb'

urlpatterns = [
    re_path(r'^language/activate/(?P<language_code>[ES|es|DE|de|EN|en]{2,2})/?', ActivateLanguageView.as_view(), name='activate_language'),
    re_path(r'^health/', include(health.urls)),
    re_path(r'^administration/', include(administration.urls)),
    re_path(r'^$', RedirectView.as_view(url='home')),
    re_path(r'^home', views.home, name='home'),
    re_path(r'^earkweb/version', views.version, name='version'),
    re_path(r'^access/', include('access.urls')),
    re_path(r'^submission/', include('submission.urls')),
    re_path(r'^management/', include('management.urls')),
    re_path(r'^admin', admin.site.urls),
    re_path(r'^api/?', include('api.urls')),
    re_path(r'^rs/?', include('resourcesync.urls')),
    re_path(r'^oai/?', include('oai_pmh.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    re_path(r'^check_folder_exists/(?P<folder>[0-0a-zA-Z_/]{3,200})/$', views.check_folder_exists, name='check_folder_exists'),
    re_path(r'^check_submission_exists/(?P<package_name>[0-9a-zA-Z-_/\.]{3,200})/$', views.check_submission_exists, name='check_submission_exists'),
    re_path(r'^check_identifier_exists/(?P<identifier>[0-9a-zA-Z-_/\.\:]{1,200})/$', views.check_identifier_exists, name='check_identifier_exists'),
    re_path(r'^read-file/(?P<ip_sub_file_path>.*)/$', views.read_file, name='read-file'),
    re_path(r'^get_directory_json/$', views.get_directory_json, name='get_directory_json'),
    re_path(r'^get_storage_directory_json$', views.get_storage_directory_json, name='get_storage_directory_json'),
    re_path(r'^poll_state/$', views.poll_state, name='poll_state'),
    re_path(r'^solrif/(?P<core>[0-9a-zA-Z-]{3,200})/(?P<operation>[0-9a-zA-Z-]{3,200})/$', views.solrif, name='solrif'),

    re_path(r'^howto/$', views.howto_overview, name='howto'),
    re_path(r'^howto-create-dataset/$', views.howto_create_dataset, name='howto_create_dataset'),
    re_path(r'^howto-ingest-dataset/$', views.howto_ingest_dataset, name='howto_ingest_dataset'),
    re_path(r'^howto-use-the-api/$', views.howto_use_the_api, name='howto_use_the_api'),

    path('wordcloud/', views.WordCloudView.as_view(), name='wordcloud'),
    path('chart', views.line_chart, name='line_chart'),
    path('chartJSON', views.line_chart_json, name='line_chart_json'),

    re_path(r'^oai-pmh/$', views.oai_pmh, name='oai-pmh'),

    re_path(r'^resource-sync/$', views.resource_sync, name='resource-sync'),
]

urlpatterns = [
    re_path(r'^$', RedirectView.as_view(url='earkweb/')),
    re_path(r'^earkweb/', include(urlpatterns)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# print configuration parameters at application startup
log_current_configuration()