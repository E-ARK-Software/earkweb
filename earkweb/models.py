#!/usr/bin/env python
# coding=UTF-8
import logging
from urllib.request import urlopen
from access.search.solrquery import SolrQuery
from access.search.solrserver import SolrServer
from config.configuration import solr_host, solr_protocol
from config.configuration import solr_port
from config.configuration import solr_core
from django.contrib.auth.models import User
from django.db import models
from taggit.managers import TaggableManager
import json


class RepoUser(models.Model):
    class Meta:
        db_table = 'repouser'
    id = models.AutoField(primary_key=True)    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    org_nsid = models.CharField(max_length=100)
    confirmed = models.BooleanField(default=False)
    confirmation_status = models.IntegerField(default=0)


class InformationPackage(models.Model):
    class Meta:
        db_table = 'informationpackage'
    id = models.AutoField(primary_key=True)
    uid = models.CharField(max_length=200, unique=True)
    package_name = models.CharField(max_length=200)
    identifier = models.CharField(max_length=200)
    external_id = models.CharField(max_length=200)
    tags = TaggableManager()
    parent_id = models.CharField(max_length=200)
    version = models.IntegerField()
    work_dir = models.CharField(max_length=4096)
    storage_dir = models.CharField(max_length=4096)
    basic_metadata = models.TextField(blank=True, null=True)
    last_change = models.DateTimeField(auto_now_add=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, blank=True)
    deleted = models.BooleanField(default=False)

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def num_indexed_docs_storage(self):
        if not self.identifier:
            return 0
        else:
            try:
                #
                query_part = "package:%22" + str(self.identifier) + "%22"
                sq = SolrQuery(SolrServer(solr_protocol, solr_host, solr_port))
                query_url_pattern = sq.get_select_pattern(solr_core)
                query_ulr = query_url_pattern.format(query_part)
                logging.debug("Solr query: %s" % query_ulr)
                data = json.load(urlopen(query_ulr))
                return int(data['response']['numFound'])
            except ValueError:
                return 0

    def __str__(self):
        return self.work_dir


class Representation(models.Model):

    class Meta:
        db_table = 'representations'

    id = models.AutoField(primary_key=True)
    identifier = models.CharField(max_length=200)
    label = models.CharField(max_length=200)
    description = models.CharField(max_length=4096)
    file_metadata = models.TextField(blank=True, null=True, default='{}')
    license = models.CharField(max_length=200)
    accessRights = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True, blank=True)
    ip = models.ForeignKey(InformationPackage, on_delete=models.CASCADE, null=True)


class InternalIdentifier(models.Model):
    class Meta:
        db_table = 'internalidentifier'
    id = models.AutoField(primary_key=True)
    org_nsid = models.CharField(max_length=200)
    identifier = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True, blank=True)
    used = models.BooleanField(default=False)
    is_blockchain_id = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return "%s:%s" % (self.org_nsid, self.identifier)


class UploadedFile(models.Model):
    id = models.AutoField(primary_key=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
    creation_datetime = models.DateTimeField(auto_created=True, blank=True, null=True)
    title = models.CharField(max_length=100)
    file = models.FileField(max_length=200, upload_to="tmp")
    sha256 = models.CharField(max_length=64, db_index=True)

    def save(self, *args, **kw_args):
        super(UploadedFile, self).save(*args, **kw_args)


class VocabularyType(models.Model):

    class Meta:
        db_table = 'vocabularytype'

    type = models.CharField(primary_key=True, max_length=20)

    def __str__(self):
        return self.type


class Vocabulary(models.Model):

    class Meta:
        db_table = 'vocabulary'

    id = models.AutoField(primary_key=True)
    type = models.ForeignKey(VocabularyType, related_name='vocabulary', on_delete=models.CASCADE)
    term = models.CharField(max_length=200)

    def __str__(self):
        return "%s:%s" % (self.type, self.term)


class TestModel(models.Model):
    class Meta:
        db_table = 'testmodel'
    # primary key database
    id = models.AutoField(primary_key=True)
    # internal IP identifier
    firstname = models.CharField(max_length=200)
    # public IE identifier
    lastname = models.CharField(max_length=200)

    def __str__(self):
        return self.id

# pylint: disable=no-member