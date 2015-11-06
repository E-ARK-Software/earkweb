import os
from django.db import models
from workflow.models import WorkflowModules
from datetime import datetime

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
    packagename = models.CharField(max_length=200)
    path = models.CharField(max_length=4096)
    storage_loc = models.CharField(max_length=4096)
    statusprocess = models.IntegerField(null=True, choices=StatusProcess_CHOICES)
    last_task = models.ForeignKey(WorkflowModules, default="DefaultTask")
    last_change = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return self.path
