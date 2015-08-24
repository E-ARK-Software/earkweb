from django.db import models

StatusProcess_CHOICES = (
    (-1, 'Undefined'),
    (0, 'New object'),
    (100, 'SIP Delivery Validation'),
    (190, 'SIP Delivery Validation Error'),
    (200, 'Identifier assignment'),
    (300, 'SIP extraction'),
    (400, 'SIP Structure Validation'),
    (490, 'SIP Structure Validation Error'),
    (500, 'Create AIP package'),
    (590, 'AIP create failed'),
    (600, 'Create package checksum'),
    (690, 'AIP checksum created OK'),
    (600, 'AIP validate'),
    (710, 'AIP validate failed'),
    (720, 'AIP validate OK'),
)

class InformationPackage(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.CharField(max_length=200,unique=True)
    packagename = models.CharField(max_length=200,unique=True)
    path = models.CharField(max_length=200,unique=True)
    statusprocess = models.IntegerField(null=True, choices=StatusProcess_CHOICES)
    def __str__(self):
        return self.path
