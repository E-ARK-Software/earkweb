from django.db import models

class MyModel(models.Model):
     fn = models.CharField(max_length=255)
     ln = models.CharField(max_length=255)

     def __unicode__(self):
      return "MyModel<%s, %s>" % (self.fn, self.ln)