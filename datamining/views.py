import os
import traceback
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
import logging
logger = logging.getLogger(__name__)
from .forms import SolrQuery, NERSelect, CSelect, ArchivePath
from workers.tasks import DMMainTask
from workers.default_task_context import DefaultTaskContext
# from config.configuration import lily_content_access_core, lily_content_access_ip, lily_content_access_port
# from config.configuration import access_solr_core, access_solr_server_ip, access_solr_port
from config.configuration import storage_solr_core, storage_solr_port, storage_solr_server_ip
import uuid
import requests
import sys

@login_required
@csrf_exempt
def start(request):
    template = loader.get_template('datamining/start.html')
    solr_query_form = SolrQuery()
    ner_model_select = NERSelect()
    # categoriser_select = CSelect()
    tar_path = ArchivePath()
    context = RequestContext(request, {
        'solr_query_form': solr_query_form,
        'ner_model_select': ner_model_select,
        # 'categoriser_select': categoriser_select,
        'tar_path_form': tar_path
    })
    return HttpResponse(template.render(context))


# def build_query(package_id, content_type, add_and, add_and_not):
def build_query(package_id, content_type):
    """
    Takes the package id and content type from the web interface and constructs a Solr query from it.

    @param package_id:      Package id
    @param content_type:    Content type (Solr specific)
    @return:                A Solr query
    """

    # solr_lily = 'http://%s:%s/solr/%s/admin/ping' % (lily_content_access_ip, lily_content_access_port, lily_content_access_core)
    # solr_local = 'http://%s:%s/solr/%s/admin/ping' % (access_solr_server_ip, access_solr_port, access_solr_core)
    # if requests.get(solr_lily).status_code == 200:
    #     solr_prefix = 'http://%s:%s/solr/%s/select?q=' % (lily_content_access_ip, lily_content_access_port, lily_content_access_core)
    # elif requests.get(solr_local).status_code == 200:
    #     solr_prefix = 'http://%s:%s/solr/%s/select?q=' % (access_solr_server_ip, access_solr_port, access_solr_core)

    solr_storage = 'http://%s:%s/solr/%s/admin/ping' % (storage_solr_server_ip, storage_solr_port, storage_solr_core)
    if requests.get(solr_storage).status_code == 200:
        solr_prefix = 'http://%s:%s/solr/%s/select?q=' % (storage_solr_server_ip, storage_solr_port, storage_solr_core)
    else:
        logger.error('No Solr instance is reachable.')
        solr_prefix = ''

    q_and = ' AND '
    # q_or = ' OR '
    # q_not = 'NOT '

    # Lily-Solr
    q_package_id = 'path:%s' % package_id
    q_content_type = 'contentType:\"%s\"' % content_type

    # Solr 6
    # q_package_id = 'package:%s' % package_id
    # q_content_type = 'content_type:\"%s\"' % content_type

    solr_query = solr_prefix + q_package_id + q_and + q_content_type + '&wt=json'

    return solr_query


@login_required
@csrf_exempt
def celery_nlp_new_collection(request):
    """
    Create a new collection (get documents via Solr requests) and start NLP.

    @param request:
    @return:
    """
    if request.method == 'POST':
        # template = loader.get_template('datamining/start.html')
        # context = RequestContext(request, {
        #
        # })
        try:
            logger.debug('Received POST: ', request.POST)
            # print request.POST
            package_id = request.POST['package_id']
            content_type = request.POST['content_type']
            # additional_and = request.POST['additional_and']
            # additional_and_not = request.POST['additional_and_not']
            tar_path = request.POST['tar_path']

            # build the query
            # solr_query = build_query(package_id, content_type, additional_and, additional_and_not)
            solr_query = build_query(package_id, content_type)
            # print solr_query
            logger.debug('Solr query: %s' % solr_query)

            ner_model = request.POST['ner_model']
            # category_model = request.POST['category_model']

            datamining_main = DMMainTask()
            taskid = uuid.uuid4().__str__()
            details = {'solr_query': solr_query,
                       'ner_model': ner_model,
                       # 'category_model': category_model,
                       'tar_path': tar_path}
            print details
            # use kwargs, those can be seen in Celery Flower
            t_context = DefaultTaskContext('', '', 'workers.tasks.DMMainTask', None, '', None)
            datamining_main.apply_async((t_context,), kwargs=details, queue='default', task_id=taskid)

        except Exception, e:
            logger.debug(e.message)
            # display error message to user
            template = loader.get_template('datamining/feedback.html')
            context = RequestContext(request, {
                'status': 'An error occurred: %s' % e.message
            })
            return HttpResponse(template.render(context))

        template = loader.get_template('datamining/feedback.html')
        context = RequestContext(request, {
            'status': 'NLP processing has been initiated.'
        })
        return HttpResponse(template.render(context))
    else:
        pass
    # TODO: feedback about what happens


@login_required
@csrf_exempt
def celery_nlp_existing_collection(request):
    """
    Use an existing document collection to perform NLP on.

    @param request:
    @return:
    """
    if request.method == 'POST':
        # template = loader.get_template('datamining/start.html')
        # context = RequestContext(request, {
        #
        # })
        try:
            logger.debug('Received POST: ', request.POST)
            # print request.POST

            tar_path = request.POST['tar_path']
            ner_model = request.POST['ner_model']
            # category_model = request.POST['category_model']

            datamining_main = DMMainTask()
            taskid = uuid.uuid4().__str__()
            details = {'ner_model': ner_model,
                       # 'category_model': category_model,
                       'tar_path': tar_path}
            print details
            # use kwargs, those can be seen in Celery Flower
            t_context = DefaultTaskContext('', '', 'workers.tasks.DMMainTask', None, '', None)
            datamining_main.apply_async((t_context,), kwargs=details, queue='default', task_id=taskid)

        except Exception, e:
            logger.debug(e.message)
            # display error message to user
            template = loader.get_template('datamining/feedback.html')
            context = RequestContext(request, {
                'status': 'An error occurred: %s' % e.message
            })
            return HttpResponse(template.render(context))

        template = loader.get_template('datamining/feedback.html')
        context = RequestContext(request, {
            'status': 'NLP processing has been initiated.'
        })
        return HttpResponse(template.render(context))
    else:
        pass
    # TODO: feedback about what happens

