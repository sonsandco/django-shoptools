import logging
import traceback

from django.utils import timezone

try:
    from celery import shared_task
    from django_celery_results.models import TaskResult
except ImportError:
    USE_CELERY = False
else:
    USE_CELERY = True

from emails.models import Email
from emails.emails import \
    send_email, create_message, create_email_record_from_message


@shared_task(bind=True)
def _send_email(self, message, email_record):
    """
    This returns the task_scheduler_id for consistency with the failure case
    which non-optionally passes that to email_outcome.
    """
    if email_record.status == email_record.STATUS_PENDING:
        message.send()
    return self.request.id


@shared_task(bind=True)
def email_outcome(self, task_scheduler_id):
    result = TaskResult.objects.get(task_id=task_scheduler_id)
    email_record = Email.objects.get(task_scheduler_id=task_scheduler_id)

    if email_record.status == email_record.STATUS_PENDING:
        if result.status == 'SUCCESS':
            email_record.status = email_record.STATUS_SENT
            email_record.status_updated = timezone.now()
            email_record.save()
        elif result.status == 'FAILURE':
            log = logging.getLogger('email_error')
            if log:
                log.error('Email send failed', extra={
                    'traceback': traceback.format_exc()
                })
            email_record.status = email_record.STATUS_FAILED
            email_record.status_updated = timezone.now()
            email_record.error_message = result.traceback
            email_record.save()
        elif result.status == 'REVOKED':
            email_record.status = email_record.STATUS_CANCELLED
            email_record.status_updated = timezone.now()
            email_record.save()


def send_async_email(email_type, template_dir, recipients, related_obj=None,
                     cc=[], bcc=[], fail_silently=False, using_celery=None,
                     **context_dict):
    """
    Sends an email using celery if both celery and django_celery_results are
    available, otherwise sends it using emails.send_email.
    """
    if using_celery is None:
        using_celery = USE_CELERY
    if not using_celery:
        return send_email(email_type, template_dir, recipients,
                          related_obj=related_obj, cc=cc, bcc=cc,
                          fail_silently=fail_silently, **context_dict)

    message = create_message(email_type, template_dir, recipients, cc=[],
                             bcc=[], **context_dict)
    email_record = create_email_record_from_message(
        message, email_type, related_obj=related_obj)

    sig = _send_email.s(message, email_record)
    email_record.task_scheduler_id = sig.freeze().id
    email_record.save()
    sig.apply_async(link=email_outcome.s(), link_error=email_outcome.s())

    return True
