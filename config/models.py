from django.db import models

class Path(models.Model):
    entity  = models.CharField( max_length = 255, unique=True )
    value   = models.CharField( max_length = 255 )

    class Meta:
        ordering = ["entity"]