# -*- coding: utf-8 -*-
import json
from django.http import HttpResponse, HttpResponseRedirect

from .util import get_session, regions_data
from .models import Region


def change_region(request):
    info = get_session(request)

    # just modify the session (not a cookie) since django sessions are
    # persistent by default
    region_id = request.POST.get('region_id')

    if region_id and Region.objects.filter(pk=region_id):
        info['region_id'] = region_id
        request.session.modified = True
        success = True
    else:
        success = False

    if request.is_ajax():
        return HttpResponse(json.dumps({
            'success': success,
            'regions': regions_data(request),
        }), content_type="application/json")
    else:
        next_url = request.POST.get('next')
        return HttpResponseRedirect(next_url or '/')
