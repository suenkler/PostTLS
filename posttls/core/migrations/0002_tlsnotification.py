# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TLSNotification',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('queue_id', models.CharField(max_length=20, verbose_name='Queue ID')),
                ('notification', models.DateTimeField(verbose_name='Notification')),
            ],
        ),
    ]
