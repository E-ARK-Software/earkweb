from django.urls import re_path, path
from access import views

app_name = 'access'

urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^index$', views.index, name='index'),
    re_path(r'^search$', views.search, name='search'),
    re_path(r'^get-item/(?P<identifier>[a-zA-Z0-9\_\-\:\.,=+]{20,200})/(?P<entry>[0-9a-zA-Z_\-/\. \:]{3,500})/$',
        views.get_information_package_item, name='access_aip_item'),
    re_path(r'^indexing-task-status/(?P<task_id>.+)/$', views.indexing_task_status, name='indexing-task-status'), 
    re_path(r'^(?P<identifier>[a-zA-Z0-9\_\-\:\.,/=+]{10,500})/$', views.InformationPackageDetail.as_view(), name='asset'),
    re_path(r'^indexing-status$', views.indexingstatus, name='indexing-status'),
    re_path(r'^reindex-storage/$', views.reindex_storage, name='reindex-storage'), 
    re_path(r'^start-indexing/(?P<pk>\d+)$', views.start_indexing, name='start-indexing'),
]
