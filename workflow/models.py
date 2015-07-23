from django.db import models

class WorkflowModules(models.Model):
    identifier = models.CharField(max_length=200)
    model_definition = models.TextField()
    def __str__(self):
        return self.identifier
