# -*- coding: utf-8 -*-
"""
Basic example email module which generates and sends an email.
"""

from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.apps import apps


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


def send_email(email_type, template_dir, recipients, cc=[], bcc=[],
               fail_silently=False, **context_dict):
    from_email = context_dict.get('from_email', settings.DEFAULT_FROM_EMAIL)
    subject, text, html = email_content(email_type, template_dir,
                                        **context_dict)

    message = EmailMultiAlternatives(subject, text, from_email, recipients,
                                     cc=cc, bcc=bcc)
    if html:
        message.attach_alternative(html, 'text/html')

    return message.send(fail_silently=fail_silently)
