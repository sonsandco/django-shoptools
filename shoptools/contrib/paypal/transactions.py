import paypalrestsdk

from django.conf import settings
from django.shortcuts import redirect, get_object_or_404
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from .models import Transaction


def get_transaction(secret):
    return get_object_or_404(Transaction, secret=secret)


def _get_setting(name):
    return getattr(settings, name,
                   Exception('Please specify %s in settings.' % name))


PAYPAL_MODE = _get_setting('PAYPAL_MODE')
PAYPAL_CLIENT_ID = _get_setting('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = _get_setting('PAYPAL_CLIENT_SECRET')

import logging
logging.basicConfig(level=logging.DEBUG)

paypalrestsdk.configure({
    'mode': PAYPAL_MODE,
    'client_id': PAYPAL_CLIENT_ID,
    'client_secret': PAYPAL_CLIENT_SECRET
})

DEFAULT_PARAMS = {
    'intent': 'sale',
    'payer': {
        'payment_method': 'paypal',
    }
}


def create_payment(trans, params):
    merged_params = {}
    merged_params.update(DEFAULT_PARAMS)

    # Handling billing and shipping addresses correctly within Paypal requires
    # PayPal Payments Pro, which is only available in US, UK, and Canada.
    # Therefore we handle the addresses ourself, and send a profile telling
    # Paypal not to ask the user for their address.
    web_profile = None
    profile_name = 'django-paypal-profile'
    web_profiles = paypalrestsdk.WebProfile.all()
    try:
        for profile in web_profiles:
            if profile.name == profile_name:
                web_profile = profile
                break
    except KeyError:
        pass

    if not web_profile:
        web_profile = paypalrestsdk.WebProfile({
            'name': profile_name,
            'input_fields': {
                'no_shipping': 1
            },
        })

        if not web_profile.create():
            web_profile = None

    # If there isn't a profile for any reason, we can still proceed. It means
    # the user will have to enter their address again and will cause confusion
    # if they use a different address than they entered in the checkout view,
    # but that is unlikely to happen and probably preferable to not completing
    # the transaction.
    if web_profile:
        merged_params.update({
            'experience_profile_id': web_profile.id,
        })

    merged_params.update(params)

    payment = paypalrestsdk.Payment(merged_params)

    # Create Payment and return status
    if payment.create():
        # Save payment id to the transaction
        trans.status = Transaction.CREATED
        trans.paypalrestsdk_id = payment.id
        trans.save()

        # Redirect the user to given approval url
        for link in payment.links:
            if link.rel == 'approval_url':
                # Convert to str to avoid google appengine unicode issue
                # https://github.com/paypal/rest-api-sdk-python/pull/58
                approval_url = str(link.href)
                return redirect(approval_url)
    else:
        # PB TODO: Generic error page
        print ('Error while creating payment:')
        print (payment.error)
        return redirect('checkout_checkout')


def execute_payment(trans, request):
    # ID of the payment. This ID is provided when creating payment.
    payment = paypalrestsdk.Payment.find(trans.paypalrestsdk_id)
    payer_id = request.GET.get('PayerID')

    return payment.execute({'payer_id': payer_id})


def make_payment(content_object, request=None, transaction_opts={},
                 get_return_url=None):
    intent = transaction_opts.get('intent',
                                  DEFAULT_PARAMS.get('intent')).lower()
    trans = Transaction(content_object=content_object, intent=intent)

    total = content_object.get_amount()
    shipping = content_object.shipping_cost
    subtotal = (total - shipping)

    params = {
        'transactions': [{
            'amount': {
                'total': '%.2f' % total,
                'currency': content_object.get_currency()[0],
                'details': {
                    'subtotal': '%.2f' % subtotal,
                    'shipping': '%.2f' % shipping,
                }
            },
            'item_list': {'items': []},
        }],
    }

    for line in content_object.get_lines():
        params['transactions'][0]['item_list']['items'].append({
            'name': line.description,
            'quantity': line.quantity,
            'price': '%.2f' % float(line.total / line.quantity),
            'currency': content_object.get_currency()[0],
        })

    if request:
        if get_return_url:
            return_url = get_return_url(trans)
        else:
            return_url = reverse('paypal_execute_transaction',
                                 args=(trans.secret, ))

        return_url = ''.join((
            'https://' if request.is_secure() else 'http://',
            request.META['HTTP_HOST'],
            return_url,
        ))

        cancel_url = ''.join((
            'https://' if request.is_secure() else 'http://',
            request.META['HTTP_HOST'],
            request.get_full_path()
        ))

        params.update({
            'redirect_urls': {
                'return_url': return_url,
                'cancel_url': cancel_url,
            }
        })
    else:
        # PB TODO
        raise NotImplementedError

    params.update(transaction_opts)

    if request:
        return create_payment(trans, params)
    else:
        # PB TODO
        raise NotImplementedError
