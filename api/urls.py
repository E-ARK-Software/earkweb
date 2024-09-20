from api import views
from django.urls import re_path, path
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
    re_path(r'^(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # endpoints with database access only

    #re_path(r'^identifiers/$', views.int_id_list),
    #re_path(r'^identifiers/byextuid/$', views.identifiers_by_extuid),

    re_path(r'^ips/$', views.InformationPackages.as_view()),
    re_path(r'^ips/%s/$' % representations_directory, views.representations_list),

    re_path(r'^ips/(?P<uid>[a-z0-9\-]{36,36})/$', views.InfPackDetail.as_view()),

    # endpoints which use backend tasks to operate on the working area

    re_path(r'^ips/(?P<uid>[a-z0-9\-]{36,36})/(?P<representation>[a-z0-9\-]{40,40})/rename/$',
        views.rename_representation),

    re_path(r'^ips/(?P<uid>[a-z0-9\-]{36,36})/create-package$', views.create_package),

    re_path(r'^ips/(?P<uid>[a-z0-9\-]{36,36})/startingest$', views.start_ingest),

    re_path(r'^ips/(?P<uid>[a-z0-9\-]{36,36})/(?P<representation_id>[a-z0-9\-]{40,40})/$',
        views.do_informationpackage_representation),

    # endpoints which require direct access the working area

    re_path(r'^ips/(?P<uid>[a-z0-9\-]{36,36})/representations/info/$',
        views.informationpackage_representations_info),

    re_path(r'^ips/(?P<uid>[a-z0-9\-]{36,36})/representation/(?P<representation_label>[A-Za-z0-9\-]{3,100})/info/$',
        views.informationpackage_representation_info_by_label),

    re_path(r'^ips/(?P<uid>[a-z0-9\-]{36,36})/file-resource/(?P<ip_sub_file_path>.*)/$',
        views.do_working_dir_file_resource),

    re_path(r'^ips/(?P<identifier>[a-zA-Z0-9\_\-\:\.,=+]{20,200})/(?P<entry>[0-9a-zA-Z_\-/\. \:]{3,500})/stream/$',
        views.package_entry_from_backend, name='read_container_package_entry'),

    re_path(r'^ips/status/$', views.get_ip_states),
    re_path(r'^ips/(?P<uid>[a-z0-9\-]{36,36})/status/$', views.get_ip_state),

    re_path(r'^ips/(?P<uid>[a-z0-9\-]{36,36})/'
        r'(?P<representation>[a-z0-9\-]{3,50})/(?P<datatype>[a-z0-9]{3,20})/upload/$',
        views.UploadFile.as_view()),
    re_path(r'^ips/(?P<uid>[a-z0-9\-]{36,36})/(?P<datatype>[a-z0-9]{1,20})/upload/$',
        views.UploadFile.as_view()),

    re_path(r'^ips/(?P<uid>[a-z0-9\-]{36,36})/dir-json$', views.do_working_dir_dir_json),

    # endpoints which require direct access to the storage backend

    # (?P<identifier>[a-z0-9\-:/\.,=+]{20,80})
    re_path(r'^ips/(?P<identifier>[a-zA-Z0-9\_\-\:/\.,=+]{20,200})/file-resource/(?P<ip_sub_file_path>.*)/$',
        views.do_storage_file_resource),

    re_path(r'^storage/ips/(?P<identifier>[a-zA-Z0-9\_\-\:/\.]{20,200})/dir-json$', views.do_storage_dir_json),
    re_path(r'^storage/(?P<identifier>[a-zA-Z0-9\_\-\:/\.]{20,200})/%s/$' % representations_directory,
        views.get_ip_representations_info, name='storage_identifier_representations'),
    re_path(r'^storage/ips/(?P<identifier>[a-zA-Z0-9\_\-\:/\.]{20,200})/index/$', views.index_informationpackage),

    # endpoints which require direct access to both, working area and storage backend

    re_path(r'^ips/(?P<identifier>[a-zA-Z0-9\_\-\:/\.]{20,200})/checkout-working-copy/$',
        views.checkout_working_copy),

]
