import os
from django.db import models
from workflow.models import WorkflowModules

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
    path = models.CharField(max_length=200)
    statusprocess = models.IntegerField(null=True, choices=StatusProcess_CHOICES)
    last_task = models.ForeignKey(WorkflowModules)
    def __str__(self):
        return self.path
