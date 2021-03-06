# Generated by Django 2.1 on 2018-08-08 04:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.PositiveSmallIntegerField(choices=[(1, 'Pending'), (2, 'Sent'), (3, 'Failed'), (4, 'Cancelled')], default=1)),
                ('status_updated', models.DateTimeField()),
                ('queued_until', models.DateTimeField(blank=True, null=True)),
                ('email_type', models.CharField(max_length=191)),
                ('sent_from', models.CharField(max_length=255)),
                ('subject', models.CharField(max_length=255)),
                ('recipients', models.TextField()),
                ('cc_to', models.TextField(blank=True, default='')),
                ('bcc_to', models.TextField(blank=True, default='')),
                ('reply_to', models.TextField(blank=True, default='')),
                ('text', models.TextField()),
                ('html', models.TextField(blank=True, default='')),
                ('error_message', models.TextField(blank=True, default='')),
                ('task_scheduler_id', models.CharField(blank=True, db_index=True, default='', editable=False, max_length=255)),
                ('related_obj_id', models.PositiveIntegerField(blank=True, editable=False, null=True)),
                ('related_obj_content_type', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ('-status_updated',),
            },
        ),
    ]
