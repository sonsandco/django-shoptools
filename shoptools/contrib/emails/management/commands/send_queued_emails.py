import traceback
import logging

from django.core.management.base import NoArgsCommand
from django.utils import timezone

from emails.models import Email
from emails.emails import create_message_from_email_record


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        for email in Email.objects.filter(
                status=Email.STATUS_PENDING,
                queued_until__lte=timezone.now()):

            message = create_message_from_email_record(email)

            try:
                message.send()
                email.status = Email.STATUS_SENT
                email.queued_until = None
                email.status_updated = timezone.now()
                email.save()
            except Exception:
                log = logging.getLogger('email_error')
                if log:
                    log.error('Email send failed', extra={
                        'traceback': traceback.format_exc()
                    })
                email.status = Email.STATUS_FAILED
                email.error_message = traceback.format_exc()
                email.status_updated = timezone.now()
                email.save()
