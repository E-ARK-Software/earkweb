from django.urls import re_path, path
from access import views

from config.configuration import identifier_pattern, entry_pattern


app_name = 'access'

urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^index$', views.index, name='index'),
    re_path(r'^search$', views.search, name='search'),
    re_path(fr'^(?P<identifier>{identifier_pattern})/get-item/(?P<entry>{entry_pattern})/$',
        views.get_information_package_item, name='access_aip_item'),
    re_path(r'^indexing-task-status/(?P<task_id>.+)/$', views.indexing_task_status, name='indexing-task-status'), 
    re_path(r'^ips_table$', views.informationpackages_overview, name='ips_table'),
    re_path(fr'^(?P<identifier>{identifier_pattern})/$', views.InformationPackageDetail.as_view(), name='asset'),
    re_path(r'^indexing-status$', views.indexingstatus, name='indexing-status'),
    re_path(r'^reindex-storage/$', views.reindex_storage, name='reindex-storage'), 
    re_path(r'^start-indexing/(?P<pk>\d+)$', views.start_indexing, name='start-indexing'),
    re_path(r'^num-indexed/(?P<pk>\d+)$', views.num_indexed, name='num-indexed'),
]
