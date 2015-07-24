from django.db import models
import uuid

class WorkflowModules(models.Model):
    identifier = models.CharField(max_length=200)
    model_definition = models.TextField()
    def __str__(self):
        return self.identifier

class Wirings(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200,unique=True)
    working = models.TextField()
    language = models.CharField(max_length=200)
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'wirings'