import traceback
import logging

from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.apps import apps

from .models import Email


def get_current_site():
    if not apps.is_installed('django.contrib.sites'):
        return None

    from django.contrib.sites.models import Site
    return Site.objects.get_current()


def email_content(email_type, template_dir, **context):
    """Return tuple of subject, text content and html content for a given email
       type and context."""
    context.update({
        'site': get_current_site(),
    })
    subject = render_to_string(template_dir + '%s_subject.txt' % email_type,
                               context)
    context['subject'] = subject
    text_content = render_to_string(template_dir + '%s.txt' % email_type,
                                    context)

    context['text_content'] = text_content
    try:
        html_content = render_to_string(template_dir + '%s.html' % email_type,
                                        context)
    except TemplateDoesNotExist:
        html_content = None

    return (subject.strip(), text_content,
            html_content if html_content else None)


def create_message(email_type, template_dir, recipients, cc=[], bcc=[],
                   **context_dict):
    reply_to = context_dict.get('reply_to',
                                getattr(settings, 'EMAIL_REPLY_TO', []))
    if reply_to:
        reply_to = [reply_to]
    from_email = context_dict.get('from_email', settings.DEFAULT_FROM_EMAIL)
    subject, text, html = email_content(email_type, template_dir,
                                        **context_dict)

    message = EmailMultiAlternatives(subject, text, from_email, recipients,
                                     cc=cc, bcc=bcc, reply_to=reply_to)
    if html:
        message.attach_alternative(html, 'text/html')
    return message


def create_message_from_email_record(email_record):
    recipients = email_record.recipients.split(', ')
    cc = email_record.cc_to.split(', ')
    bcc = email_record.bcc_to.split(', ')
    reply_to = email_record.reply_to.split(', ')

    message = EmailMultiAlternatives(email_record.subject, email_record.text,
                                     email_record.sent_from, recipients,
                                     cc=cc, bcc=bcc, reply_to=reply_to)
    if email_record.html:
        message.attach_alternative(email_record.html, 'text/html')
    return message


def create_email_record(email_type, template_dir, recipients, cc=[], bcc=[],
                        related_obj=None, **context_dict):
    reply_to = context_dict.get('reply_to',
                                getattr(settings, 'EMAIL_REPLY_TO', []))
    if reply_to:
        reply_to = [reply_to]
    from_email = context_dict.get('from_email', settings.DEFAULT_FROM_EMAIL)
    subject, text, html = email_content(email_type, template_dir,
                                        **context_dict)

    email_record = Email(status_updated=timezone.now(),
                         email_type=email_type,
                         sent_from=from_email,
                         subject=subject,
                         recipients=', '.join(recipients),
                         cc_to=', '.join(cc),
                         bcc_to=', '.join(bcc),
                         reply_to=', '.join(reply_to),
                         text=text)
    if html:
        email_record.html = html

    if related_obj:
        email_record.related_obj_content_type = \
            ContentType.objects.get_for_model(related_obj)
        email_record.related_obj_id = related_obj.id

    email_record.save()
    return email_record


def create_email_record_from_message(message, email_type, related_obj=None):
    html = ''
    for content, mimetype in getattr(message, 'alternatives', []):
        if mimetype == 'text/html':
            html = content
    email_record = Email(status_updated=timezone.now(),
                         email_type=email_type,
                         sent_from=message.from_email,
                         subject=message.subject,
                         recipients=', '.join(message.to),
                         cc_to=', '.join(message.cc),
                         bcc_to=', '.join(message.bcc),
                         reply_to=', '.join(message.reply_to),
                         text=message.body,
                         html=html)
    if related_obj:
        email_record.related_obj_content_type = \
            ContentType.objects.get_for_model(related_obj)
        email_record.related_obj_id = related_obj.id
    email_record.save()
    return email_record


def send_email(email_type, template_dir, recipients, related_obj=None, cc=[],
               bcc=[], fail_silently=False, **context_dict):
    message = create_message(email_type, template_dir, recipients, cc=[],
                             bcc=[], **context_dict)
    email_record = create_email_record_from_message(
        message, email_type, related_obj=related_obj)

    try:
        message.send()
        if email_record:
            email_record.status = email_record.STATUS_SENT
            email_record.status_updated = timezone.now()
            email_record.save()
        return True
    except Exception as e:
        log = logging.getLogger('email_error')
        if log:
            log.error('Email send failed', extra={
                'traceback': traceback.format_exc()
            })

        if email_record:
            email_record.status = email_record.STATUS_FAILED
            email_record.error_message = traceback.format_exc()
            email_record.status_updated = timezone.now()
            email_record.save()
        if not fail_silently:
            raise e
        return False
