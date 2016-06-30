# -*- coding: utf-8 -*-

from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist


TEMPLATE_DIR = 'checkout/emails/'


def send_email_receipt(order):
    send_email('receipt', [order.email], order=order)
    send_email('notification', [t[1] for t in settings.CHECKOUT_MANAGERS],
               order=order)


def send_dispatch_email(order):
    send_email('dispatch', [order.email], order=order)


def email_content(email_type, **context):
    '''Return tuple of subject, text content and html content for a given email
       type and context.'''

    template_dir = context.pop('template_dir', TEMPLATE_DIR)

    context.update({
        'site': Site.objects.get_current(),
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


def send_email(email_type, recipients, cc=[], bcc=[], **context_dict):
    '''Send an email of a given type to email_address, using given context.'''

    from_email = context_dict.get('from_email', settings.DEFAULT_FROM_EMAIL)
    subject, text, html = email_content(email_type, **context_dict)

    message = EmailMultiAlternatives(subject, text, from_email, recipients,
                                     cc=cc, bcc=bcc)
    if html:
        message.attach_alternative(html, "text/html")
    # TODO should we be failing silently here? If not will need some way to
    # tell the user the address didn't work
    return message.send()
