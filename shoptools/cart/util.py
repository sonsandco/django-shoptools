# -*- coding: utf-8 -*-

import uuid
import importlib
from functools import partial

from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType

from . import settings as cart_settings


def get_module(name):
    module_name = getattr(cart_settings, '%s_MODULE' % name)
    return importlib.import_module(module_name) if module_name else None


get_accounts_module = partial(get_module, 'ACCOUNTS')
get_regions_module = partial(get_module, 'REGIONS')
get_shipping_module = partial(get_module, 'SHIPPING')
get_vouchers_module = partial(get_module, 'VOUCHERS')


def make_uuid():
    return uuid.uuid4()


def validate_options(ctype, pk, options):
    """Strip invalid cart line options from an options dict. """

    # TODO this will eventually take an instance, not a ctype/pk

    content_type = ContentType.objects \
        .get_by_natural_key(*ctype.split("."))
    obj = content_type.get_object_for_this_type(pk=pk)
    available = obj.available_options()
    filtered = {k: v for k, v in options.items()
                if k in available and v in available[k]}

    # print (options, available, filtered)

    return filtered


# TODO - put this somewhere else

def get_cart_html(cart, template='cart/cart_snippet.html'):
    return render_to_string(template, {
        'cart': cart
    }, request=cart.request)
