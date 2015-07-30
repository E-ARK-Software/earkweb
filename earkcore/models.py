from django.db import models

StatusProcess_CHOICES = (
    (0, 'New object'),
    (100, 'Identifier assignment'),
    (200, 'SIP extraction'),
    (300, 'SIP validate'),
    (310, 'SIP validate failed'),
    (320, 'SIP validate OK'),
    (400, 'Create AIP package'),
    (410, 'AIP create failed'),
    (420, 'AIP created OK'),
    (500, 'Create package checksum'),
    (510, 'AIP checksum created OK'),
    (600, 'AIP validate'),
    (610, 'AIP validate failed'),
    (620, 'AIP validate OK'),
)

class InformationPackage(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.CharField(max_length=200,unique=True)
    path = models.CharField(max_length=200,unique=True)
    statusprocess = models.IntegerField(null=True, choices=StatusProcess_CHOICES)
    def __str__(self):
        return self.path
