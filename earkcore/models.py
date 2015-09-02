from django.db import models

StatusProcess_CHOICES = (

    (-1, 'Undefined'),

    (0, 'New object'),

    (100, 'SIP delivery validated'),
    (190, 'SIP delivery validation failed'),

    (200, 'Identifier assignment'),
    (290, 'Identifier assignment failed'),

    (300, 'SIP extracted'),
    (390, 'SIP extraction failed'),

    (400, 'SIP validated'),
    (490, 'SIP validation failed'),

    (500, 'AIP created'),
    (590, 'AIP creation failed'),

    (600, 'AIP validated'),
    (690, 'AIP validation failed'),

    (700, 'AIP container package created'),
    (790, 'AIP container packaging failed'),

    (800, 'AIP HDFS upload successful'),
    (890, 'AIP HDFS upload failed'),

)

class InformationPackage(models.Model):
    # primary key database
    id = models.AutoField(primary_key=True)
    # internal IP identifier
    uuid = models.CharField(max_length=200)
    # public IE identifier
    identifier = models.CharField(max_length=200)
    packagename = models.CharField(max_length=200)
    path = models.CharField(max_length=200)
    statusprocess = models.IntegerField(null=True, choices=StatusProcess_CHOICES)
    def __str__(self):
        return self.path
