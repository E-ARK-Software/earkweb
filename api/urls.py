from api import views
from django.conf.urls import url
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from config.configuration import representations_directory


schema_view = get_schema_view(
   openapi.Info(
      title="Data Repository API",
      default_version='v1',
      description="Data Repository API",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="info@ait.ac.at"),
      license=openapi.License(name="MIT License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns = [

    # api

    url(r'^(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # endpoints with database access only

    #url(r'^identifiers/$', views.int_id_list),
    #url(r'^identifiers/byextuid/$', views.identifiers_by_extuid),

    url(r'^ips/$', views.InformationPackages.as_view()),
    url(r'^ips/%s/$' % representations_directory, views.representations_list),

    url(r'^ips/(?P<uid>[a-z0-9\-]{36,36})/$', views.InfPackDetail.as_view()),

    # endpoints which use backend tasks to operate on the working area

    url(r'^ips/(?P<uid>[a-z0-9\-:+]{36,50})/(?P<representation>[a-z0-9\-]{40,40})/rename/$',
        views.rename_representation),

    url(r'^ips/(?P<procid>[a-z0-9\-]{36,36})/create-package$', views.create_package),

    url(r'^ips/(?P<procid>[a-z0-9\-]{36,36})/startingest$', views.start_ingest),

    url(r'^ips/(?P<uid>[a-z0-9\-:+]{36,50})/(?P<representation_id>[a-z0-9\-]{40,40})/$',
        views.do_informationpackage_representation),

    # endpoints which require direct access the working area

    url(r'^ips/(?P<uid>[a-z0-9\-:+]{36,50})/representations/info/$',
        views.informationpackage_representations_info),

    url(r'^ips/(?P<uid>[a-z0-9\-:+]{36,50})/representation/(?P<representation_label>[A-Za-z0-9\-]{3,100})/info/$',
        views.informationpackage_representation_info_by_label),

    url(r'^ips/(?P<uid>[a-z0-9\-]{36,36})/file-resource/(?P<ip_sub_file_path>.*)/$',
        views.do_working_dir_file_resource),

    url(r'^ips/(?P<identifier>[a-z0-9\-:+]{36,50})/(?P<entry>[0-9a-zA-Z_\-/\. \:]{3,500})/stream/$',
        views.package_entry_from_backend, name='read_container_package_entry'),

    url(r'^ips/status/$', views.get_ip_states),
    url(r'^ips/(?P<uid>[a-z0-9\-]{36,36})/status/$', views.get_ip_state),

    url(r'^ips/(?P<uid>[a-z0-9\-]{36,36})/'
        r'(?P<representation>[a-z0-9\-]{3,50})/(?P<datatype>[a-z0-9]{3,20})/upload/$',
        views.UploadFile.as_view()),
    url(r'^ips/(?P<uid>[a-z0-9\-]{36,36})/(?P<datatype>[a-z0-9]{1,20})/upload/$',
        views.UploadFile.as_view()),

    url(r'^ips/(?P<uid>[a-z0-9\-]{36,36})/dir-json$', views.do_working_dir_dir_json),

    # endpoints which require direct access to the storage backend

    url(r'^ips/(?P<identifier>[a-z0-9\-:+]{45,45})/file-resource/(?P<ip_sub_file_path>.*)/$',
        views.do_storage_file_resource),

    url(r'^storage/ips/(?P<identifier>[a-z0-9\-:+]{45,45})/dir-json$', views.do_storage_dir_json),
    url(r'^storage/(?P<identifier>[a-z0-9\-:+]{36,50})/%s/$' % representations_directory,
        views.get_ip_representations_info, name='storage_identifier_representations'),
    url(r'^storage/ips/(?P<identifier>[a-z0-9\-:]{36,45})/index/$', views.index_informationpackage),

    # endpoints which require direct access to both, working area and storage backend

    url(r'^ips/(?P<identifier>[a-z0-9\-:+]{36,50})/checkout-working-copy/$',
        views.checkout_working_copy),

]
