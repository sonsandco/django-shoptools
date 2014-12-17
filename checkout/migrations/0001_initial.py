# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import paypal.models
import checkout.models
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('secret', models.CharField(default=checkout.models.make_uuid, unique=True, max_length=32, editable=False, db_index=True)),
                ('name', models.CharField(default=b'', max_length=1023, verbose_name='Your name')),
                ('email', models.EmailField(max_length=75)),
                ('street', models.CharField(max_length=1023, verbose_name='Street Name & Number')),
                ('suburb', models.CharField(max_length=255, blank=True)),
                ('postcode', models.CharField(max_length=100)),
                ('city', models.CharField(max_length=255, verbose_name='Town / City')),
                ('country', models.CharField(default='Australia', max_length=255)),
                ('currency', models.CharField(default=b'NZD', max_length=3, editable=False)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('status', models.CharField(default=b'new', max_length=32, choices=[(b'new', b'New'), (b'paid', b'Paid'), (b'payment_failed', b'Payment Failed'), (b'processing', b'Processing (external)'), (b'shipped', b'Shipped')])),
                ('amount_paid', models.DecimalField(default=0, max_digits=8, decimal_places=2)),
            ],
            options={
            },
            bases=(models.Model, paypal.models.FullTransactionProtocol),
        ),
    ]
