from django.db import models

StatusProcess_CHOICES = (
    (0, 'Receive new object'),
    (25, 'SIP validate'),
    (26, 'SIP validate failed'),
    (29, 'SIP validate OK'),
    (30, 'Create AIP package'),
    (31, 'AIP create failed'),
    (39, 'AIP created OK'),
    (40, 'Create package checksum'),
    (49, 'AIP checksum created OK'),
    (50, 'AIP validate'),
    (51, 'AIP validate failed'),
    (59, 'AIP validate OK'),
    (1000, 'Write AIP to longterm storage'),
    (1001, 'Fail to write AIP'),
    (1002, 'No empty media available'),
    (1003, 'Problem to mount media'),
    (1999, 'Write AIP OK'),
    (3000, 'Archived'),
    (5100, 'WorkArea'),
    (9999, 'Deleted'),
)

class InformationPackage(models.Model):
    id = models.AutoField(primary_key=True)
    path = models.CharField(max_length=200,unique=True)
    statusprocess = models.IntegerField(null=True, choices=StatusProcess_CHOICES)
    def __str__(self):
        return self.name