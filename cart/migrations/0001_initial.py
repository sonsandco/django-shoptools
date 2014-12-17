# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderLine',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('parent_object_id', models.PositiveIntegerField()),
                ('item_object_id', models.PositiveIntegerField()),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('quantity', models.IntegerField()),
                ('total', models.DecimalField(max_digits=8, decimal_places=2)),
                ('description', models.CharField(max_length=255, blank=True)),
                ('options', models.TextField(blank=True)),
                ('item_content_type', models.ForeignKey(related_name='orderlines_via_item', to='contenttypes.ContentType')),
                ('parent_content_type', models.ForeignKey(related_name='orderlines_via_parent', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
