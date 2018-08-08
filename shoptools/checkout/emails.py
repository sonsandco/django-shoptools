# -*- coding: utf-8 -*-

from django.conf import settings

from shoptools.util import get_email_module
email_module = get_email_module()

TEMPLATE_DIR = 'checkout/emails/'


def send_email_receipt(order):
    if email_module and hasattr(email_module, 'send_email'):
        email_module.send_email('receipt', TEMPLATE_DIR, [order.email],
                                related_obj=order, fail_silently=True,
                                order=order)
        manager_emails = getattr(settings, 'CHECKOUT_MANAGERS', [])
        if manager_emails:
            email_module.send_email('notification', TEMPLATE_DIR,
                                    [t[1] for t in manager_emails],
                                    related_obj=order, fail_silently=True,
                                    order=order)


def send_dispatch_email(order):
    if email_module and hasattr(email_module, 'send_email'):
        email_module.send_email('dispatch', TEMPLATE_DIR, [order.email],
                                related_obj=order, fail_silently=True,
                                order=order)
