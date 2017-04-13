# -*- coding: utf-8 -*-
import json
from django.http import HttpResponse, HttpResponseRedirect

from .util import get_session, shipping_data
from .models import ShippingOption


def change_shipping_option(request):
    info = get_session(request)

    # just modify the session (not a cookie) since django sessions are
    # persistent by default
    shipping_option_id = request.POST.get('shipping_option_id')

    if shipping_option_id and \
       ShippingOption.objects.filter(pk=shipping_option_id):
        info['shipping_option_id'] = shipping_option_id
        request.session.modified = True
        success = True
    else:
        success = False

    if request.is_ajax():
        return HttpResponse(json.dumps({
            'success': success,
            'shipping': shipping_data(request),
        }), content_type="application/json")
    else:
        next_url = request.POST.get('next')
        return HttpResponseRedirect(next_url or '/')
