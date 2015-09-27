# -*- coding: utf-8 -*-

from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives


TEMPLATE_DIR = 'checkout/emails/'


def send_email_receipt(order):
    send_email('receipt', [order.email], order=order)
    send_email('notification', [t[1] for t in settings.CHECKOUT_MANAGERS],
               order=order)


def email_content(email_type, **context):
    '''Return tuple of subject, text content and html content for a given email
       type and context.'''

    context.update({
        'site': Site.objects.get_current(),
    })
    subject = render_to_string(TEMPLATE_DIR + '%s_subject.txt' % email_type,
                               context)
    context['subject'] = subject
    text_content = render_to_string(TEMPLATE_DIR + '%s.txt' % email_type,
                                    context)

    context['text_content'] = text_content
    html_content = render_to_string(TEMPLATE_DIR + '%s.html' % email_type,
                                    context)

    return (subject.strip(), text_content.encode('ascii', 'ignore'),
            html_content.encode('ascii', 'ignore'))


def send_email(email_type, recipients, cc=[], bcc=[], **context_dict):
    '''Send an email of a given type to email_address, using given context.'''

    from_email = context_dict.get('from_email', settings.DEFAULT_FROM_EMAIL)
    subject, text, html = email_content(email_type, **context_dict)

    message = EmailMultiAlternatives(subject, text, from_email, recipients,
                                     cc=cc, bcc=bcc)
    message.attach_alternative(html, "text/html")
    return message.send()
