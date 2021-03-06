# -*- coding: utf-8 -*-

import uuid
import importlib
from functools import partial

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType

from shoptools import settings as shoptools_settings


def get_module(name):
    module_name = getattr(shoptools_settings, '%s_MODULE' % name)
    return importlib.import_module(module_name) if module_name else None


get_accounts_module = partial(get_module, 'ACCOUNTS')
get_regions_module = partial(get_module, 'REGIONS')
get_shipping_module = partial(get_module, 'SHIPPING')
get_vouchers_module = partial(get_module, 'VOUCHERS')
get_favourites_module = partial(get_module, 'FAVOURITES')
get_payment_module = partial(get_module, 'PAYMENT')
get_email_module = partial(get_module, 'EMAIL')


def make_uuid():
    return uuid.uuid4()


def validate_options(instance, options):
    """Strip invalid cart line options from an options dict. """

    available = dict(instance.available_options())

    def is_valid(k, v):
        if k not in available:
            return False

        # allow any user input for str options
        if available[k] is str:
            return True

        # assume an iterable of options
        return k in available and v in available[k]

    filtered = {k: v for k, v in options.items() if is_valid(k, v)}

    return filtered


def create_instance_key(instance):
    """Create a unique key for a model instance. """

    ctype = '%s.%s' % (instance._meta.app_label, instance._meta.model_name)
    return (ctype, instance.pk)


def unpack_instance_key(ctype, pk):
    """Retrieve a model instance from a unique key created by
       create_instance_key. """

    content_type = ContentType.objects.get_by_natural_key(*ctype.split('.'))
    try:
        instance = content_type.get_object_for_this_type(pk=pk)
    except ObjectDoesNotExist:
        instance = None

    return instance
