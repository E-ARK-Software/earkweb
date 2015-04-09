# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0003_package_cleanid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='package',
            name='source',
            field=models.CharField(default=b'file:///null', max_length=200),
        ),
    ]
