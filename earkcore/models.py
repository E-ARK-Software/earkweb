import logging
from earkcore.search.solrquery import SolrQuery
from earkcore.search.solrserver import SolrServer

from config.configuration import access_solr_server_ip
from config.configuration import access_solr_port
from config.configuration import access_solr_core

from config.configuration import local_solr_server_ip
from config.configuration import local_solr_port
from config.configuration import local_solr_core

from django.db import models
from workflow.models import WorkflowModules
import json
import urllib2


StatusProcess_CHOICES = (

    (-1, 'Undefined'),

    (0, 'Success'),
    (1, 'Error'),
)


class InformationPackage(models.Model):
    # primary key database
    id = models.AutoField(primary_key=True)
    # internal IP identifier
    uuid = models.CharField(max_length=200)
    # public IE identifier
    identifier = models.CharField(max_length=200)
    parent_identifier = models.CharField(max_length=200)
    packagename = models.CharField(max_length=200)
    path = models.CharField(max_length=4096)
    storage_loc = models.CharField(max_length=4096)
    statusprocess = models.IntegerField(null=True, choices=StatusProcess_CHOICES)
    last_task = models.ForeignKey(WorkflowModules, default="DefaultTask")
    last_change = models.DateTimeField(auto_now_add=True, blank=True)

    def num_indexed_docs(self):
        if not self.identifier:
            return 0
        else:
            try:
                query_part = "path%3A%22"+self.identifier+"%22"
                sq = SolrQuery(SolrServer(access_solr_server_ip, access_solr_port))
                server_solr_query_url = sq.get_select_pattern(access_solr_core)
                query_string = server_solr_query_url.format(query_part)
                logging.debug("Solr query: %s" % query_string)
                data = json.load(urllib2.urlopen(query_string))
                return int(data['response']['numFound'])
            except ValueError as verr:
                return 0

    def num_indexed_docs_storage(self):
        if not self.identifier:
            return 0
        else:
            try:
                query_part = "package%3A%22"+self.identifier+"%22"
                sq = SolrQuery(SolrServer(local_solr_server_ip, local_solr_port))
                server_solr_query_url = sq.get_select_pattern(local_solr_core)
                query_string = server_solr_query_url.format(query_part)
                logging.debug("Solr query: %s" % query_string)
                data = json.load(urllib2.urlopen(query_string))
                return int(data['response']['numFound'])
            except ValueError as verr:
                return 0

    def __str__(self):
        return self.path
