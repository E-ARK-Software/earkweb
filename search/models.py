from django.db import models

class Package(models.Model):
    identifier = models.CharField(max_length=200)
    cleanid = models.CharField(max_length=200)
    source = models.CharField(max_length=200, default="file:///dev/null")
    date_selected = models.DateTimeField('date/time when the package was selected')
    def __str__(self):               
        return self.identifier