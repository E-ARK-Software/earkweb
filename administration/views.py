# coding=utf-8
import logging
import shutil
import time

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from eatb.utils.fileutils import human_readable_size, total_directory_size

from config.configuration import flower_service_url, flower_server, flower_port, flower_path, solr_core_ping_url, \
    solr_core_url, solr_core, solr_core_overview_url, config_path_work, config_path_storage

from taskbackend.tasks import backend_available
from celery.exceptions import TimeoutError
from taskbackend.taskutils import get_celery_worker_status, flower_is_running
from util import service_available

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):

    du_work_free = shutil.disk_usage(config_path_work).free
    du_work_used = total_directory_size(config_path_work)
    du_storage_free = shutil.disk_usage(config_path_storage).free
    du_storage_used = total_directory_size(config_path_storage)
    disk_stats = {
        "work": {
            'free': {
                'bytes': du_work_free,
                'hr': human_readable_size(du_work_free)
            },
            'used': {
                'bytes': du_work_used,
                'hr': human_readable_size(du_work_used)
            },
        },
        "storage": {
            'free': {
                'bytes': du_storage_free,
                'hr': human_readable_size(du_storage_free)
            },
            'used': {
                'bytes': du_storage_used,
                'hr': human_readable_size(du_storage_used)
            },
        },
    }

    context = {
        'celery_worker_status': get_celery_worker_status(),
        'flower_status': flower_is_running(),
        'flower_api_endpoint': flower_service_url,
        'solr_available': service_available(solr_core_ping_url),
        'solr_core_url': solr_core_url,
        'solr_core': solr_core,
        'solr_core_overview_url': solr_core_overview_url,
        'disk_stats': disk_stats,
    }
    if request.method == 'POST':
        job = backend_available.delay()
        i = 0
        while True:
            if job.status == "SUCCESS":
                context["jobid"] = job.id
                context["result"] = job.result
                break
            elif job.status == "FAILURE":
                context["jobid"] = "error"
                context["result"] = "task execution failed"
                break
            if i > 5:
                context["jobid"] = "error"
                context["result"] = "timeout"
                break
            time.sleep(5)
            i = i + 1
    return render(request, 'administration/dashboard.html', context)


@login_required
def backendadmin(request):
    context = {
        'flower_host': flower_server,
        'flower_port': flower_port,
        'flower_path': flower_path,
        'celery_worker_status': get_celery_worker_status(),
        'flower_status': flower_is_running(),
        'flower_api_endpoint': flower_service_url,
    }

    return render(request, 'administration/backendadmin.html', context)
