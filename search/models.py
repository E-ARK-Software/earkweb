import os
from django.db import models

from earkcore.utils.stringutils import safe_path_string

class AIP(models.Model):
    identifier = models.CharField(max_length=200)
    cleanid = models.CharField(max_length=200)
    source = models.CharField(max_length=200, default="file:///null")
    date_selected = models.DateTimeField('date/time when the package was selected')

    def source_available(self):
        return os.path.exists(self.source)

    def __str__(self):
        return self.identifier

class DIP(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    aips = models.ManyToManyField(AIP, through='Inclusion')

    def safe_path_string(self):
        return safe_path_string(self.name)

    def __str__(self):
        return self.name

class Inclusion(models.Model):
    aip = models.ForeignKey(AIP)
    dip = models.ForeignKey(DIP)
    stored = models.BooleanField(default=False)

