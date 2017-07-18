# -*- coding: utf-8 -*-
import json
from django.http import HttpResponse, HttpResponseRedirect


from .util import set_region, regions_data


def change_region(request):
    success = set_region(request, request.POST.get('region_id'))

    if request.is_ajax():
        return HttpResponse(json.dumps({
            'success': success,
            'regions': regions_data(request),
        }), content_type="application/json")
    else:
        next_url = request.POST.get('next')
        return HttpResponseRedirect(next_url or '/')
