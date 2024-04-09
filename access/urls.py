from django.conf.urls import url
from access import views

app_name = 'access'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^index$', views.index, name='index'),
    url(r'^search$', views.search, name='search'),
    url(r'^get-item/(?P<identifier>[0-9a-zA-Z-\:+]{36,50})/(?P<entry>[0-9a-zA-Z_\-/\. \:]{3,500})/$',
        views.get_information_package_item, name='access_aip_item'),
    url(r'^(?P<identifier>[0-9a-zA-Z-\:]{36,50})/$', views.InformationPackageDetail.as_view(), name='asset'),
    url(r'^indexing-status$', views.indexingstatus, name='indexing-status'),
    url(r'^reindex-storage/$', views.reindex_storage, name='reindex-storage'),
]
