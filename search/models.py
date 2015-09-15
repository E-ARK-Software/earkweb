import os
from django.db import models
from earkcore.filesystem.fsinfo import fsize
from earkcore.utils.fileutils import remove_protocol

from earkcore.utils.stringutils import safe_path_string

class AIP(models.Model):
    identifier = models.CharField(max_length=200)
    cleanid = models.CharField(max_length=200)
    source = models.CharField(max_length=200, default="file:///null")
    date_selected = models.DateTimeField('date/time when the package was selected')

    def safe_string(self):
        return safe_path_string(self.identifier)

    def source_available(self):
        return os.path.exists(self.source)

    def source_size(self):
        if self.source_available():
            return fsize(self.source)
        else:
            return -1

    def __str__(self):
        return self.identifier

class DIP(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    aips = models.ManyToManyField(AIP, through='Inclusion')

    def safe_path_string(self):
        return safe_path_string(self.name)

    def all_aips_available(self):
        for aip in self.aips.all():
            if not aip.source_available():
                return False
        return True

    def aips_total_size(self):
        sum = 0
        if self.all_aips_available():
            for aip in self.aips.all():
                sum += aip.source_size()
            return sum
        else:
            return -1

    def __str__(self):
        return self.name

class Inclusion(models.Model):
    aip = models.ForeignKey(AIP)
    dip = models.ForeignKey(DIP)
    stored = models.BooleanField(default=False)

