from django.db import models

# Create your models here.
class MyModel(models.Model):
    fn = models.CharField(max_length=255)
    ln = models.CharField(max_length=255)

    def __unicode__(self):
        return "MyModel<%s, %s>" % (self.fn, self.ln)

JOBS = (
    ('gerNER', 'NER German'),
    ('hunNER', 'NER Hungarian'),
)

class JobSelect(models.Model):
    input_path = models.CharField(max_length=300)
    job = models.CharField(max_length=2, choices=JOBS)

# JOBS = (
#     ('gerNER', 'NER German'),
#     ('hunNER', 'NER Hungarian'),
# )
#
# class PostAd(models.Model):
#     job = models.CharField(max_length=2, choices=JOBS)
#     input = models.CharField(max_length=300)
