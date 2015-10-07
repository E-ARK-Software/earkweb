from django.db import models
import uuid

class WorkflowModules(models.Model):
    identifier = models.CharField(max_length=200, primary_key=True)
    model_definition = models.TextField()
    ordval = models.IntegerField(default=0)
    ttype = models.IntegerField(default=0)
    tstage = models.IntegerField(default=0)
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