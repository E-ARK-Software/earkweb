from django.db import models

class Package(models.Model):
    identifier = models.CharField(max_length=200)
    cleanid = models.CharField(max_length=200)
    source = models.CharField(max_length=200, default="file:///null")
    date_selected = models.DateTimeField('date/time when the package was selected')
    def __str__(self):
        return self.identifier

class DIPackage(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    packages = models.ManyToManyField(Package)
    def __str__(self):
        return self.name
