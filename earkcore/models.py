import os
from django.db import models

StatusProcess_CHOICES = (

    (-1, 'Undefined'),

    (0, 'New object'),

    (10, 'SIP structure initialized'),
    (19, 'SIP structure initialization failed'),

    (20, 'SIP package metadata created'),
    (29, 'SIP  package metadata creation failed'),

    (30, 'SIP packaged'),
    (39, 'SIP packaging failed'),
    (40, 'SIP delivery created'),
    (49, 'SIP delivery creation failed'),

    (100, 'SIP delivery validated'),
    (200, 'Identifier assignment'),
    (300, 'SIP extracted'),
    (400, 'SIP validated'),
    (500, 'AIP created'),
    (600, 'AIP validated'),
    (700, 'AIP container package created'),
    (800, 'AIP HDFS upload successful'),

    (190, 'SIP delivery validation failed'),
    (290, 'Identifier assignment failed'),
    (390, 'SIP extraction failed'),
    (490, 'SIP validation failed'),
    (590, 'AIP creation failed'),
    (690, 'AIP validation failed'),
    (790, 'AIP container packaging failed'),
    (890, 'AIP HDFS upload failed'),

    (10000, 'New DIP creation process'),

    (10100, 'AIPs aquired'),
    (10190, 'Acquisition of AIPs failed'),

    (10200, 'AIPs extracted'),
    (10290, 'Extraction of AIPs failed'),

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
