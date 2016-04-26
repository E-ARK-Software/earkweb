import os
from django.db import models
from workflow.models import WorkflowModules
from datetime import datetime
import json
import urllib2
from django.conf import settings
import logging
logger = logging.getLogger(__name__)

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
        logger.info("Get indexed docs")
        if not self.identifier:
            return 0
        else:
            try:
                logger.info("Solr query")
                query_part = "path%3A%22"+self.identifier+"%22"
                query_string = settings.SERVER_SOLR_QUERY_URL.format(query_part)
                logger.info ("Solr query string: %s" % query_string)
                data = json.load(urllib2.urlopen(query_string))
                return int(data['response']['numFound'])
            except ValueError as verr:
                return 0

    def __str__(self):
        return self.path
