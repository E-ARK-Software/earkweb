# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0002_package_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='package',
            name='cleanid',
            field=models.CharField(default='null', max_length=200),
            preserve_default=False,
        ),
    ]
