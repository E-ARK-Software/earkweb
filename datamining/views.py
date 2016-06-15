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
from sandbox.datamining.helpers.createarchive import CreateNLPArchive


@login_required
@csrf_exempt
def start(request):
    template = loader.get_template('datamining/start.html')
    solr_query_form = SolrQuery()
    ner_model_select = NERSelect()
    categoriser_select = CSelect()
    tar_path = ArchivePath()
    context = RequestContext(request, {
        'solr_query_form': solr_query_form,
        'ner_model_select': ner_model_select,
        'categoriser_select': categoriser_select,
        'tar_path_form': tar_path
    })
    return HttpResponse(template.render(context))


def build_query(package_id, content_type, additional_query):
    # TODO: additional_query is not used
    solr_prefix = 'http://localhost:8983/solr/earkstorage/select?q='
    q_and = ' AND '
    q_or = ' OR '
    q_not = 'NOT '

    q_package_id = 'package:%s' % package_id
    q_content_type = 'content_type:%s' % content_type

    solr_query = solr_prefix + q_package_id + q_and + q_content_type + '&wt=json'

    return solr_query


@login_required
@csrf_exempt
def celery_nlp(request):
    if request.method == 'POST':
        # TODO: feedback
        template = loader.get_template('datamining/start.html')
        context = RequestContext(request, {

        })
        try:
            print request.POST
            package_id = request.POST['package_id']
            content_type = request.POST['content_type']
            additional_query = request.POST['content_type']
            tar_path = request.POST['tar_path']

            solr_query = build_query(package_id, content_type, additional_query)

            category_model = request.POST['category_model']
            ner_model = request.POST['ner_model']

            archive_creator = CreateNLPArchive()
            archive_creator.get_data_from_solr(solr_query=solr_query, archive_name=tar_path)
        except Exception, e:
            # # return error message
            # context = RequestContext(request, {
            #     'status': 'ERROR: %s' % e.message
            # })
            pass
    else:
        template = loader.get_template('datamining/start.html')
        context = RequestContext(request, {

        })
    return HttpResponse(template.render(context))

