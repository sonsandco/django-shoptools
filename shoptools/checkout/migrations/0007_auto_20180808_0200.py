# Generated by Django 2.1 on 2018-08-08 02:00

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('checkout', '0006_auto_20180808_0152'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderline',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
