from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class Email(models.Model):
    STATUS_PENDING = 1
    STATUS_SENT = 2
    STATUS_FAILED = 3
    STATUS_CANCELLED = 4

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SENT, 'Sent'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    status = models.PositiveSmallIntegerField(default=STATUS_PENDING,
                                              choices=STATUS_CHOICES)
    status_updated = models.DateTimeField()

    queued_until = models.DateTimeField(blank=True, null=True)

    email_type = models.CharField(max_length=191)

    sent_from = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    recipients = models.TextField()
    cc_to = models.TextField(default='', blank=True)
    bcc_to = models.TextField(default='', blank=True)
    reply_to = models.TextField(default='', blank=True)
    text = models.TextField()
    html = models.TextField(default='', blank=True)
    error_message = models.TextField(default='', blank=True)

    task_scheduler_id = models.CharField(max_length=255, default='',
                                         blank=True, db_index=True,
                                         editable=False)

    related_obj_content_type = models.ForeignKey(
        ContentType, blank=True, null=True, on_delete=models.SET_NULL,
        editable=False)
    related_obj_id = models.PositiveIntegerField(blank=True, null=True,
                                                 editable=False)
    related_obj = GenericForeignKey('related_obj_content_type',
                                    'related_obj_id')

    def __str__(self):
        return '%s email to %s' % (self.get_status_display(), self.recipients)

    class Meta:
        ordering = ('-status_updated', )
