# -*- coding: utf-8 -*-
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.core.serializers.json import DjangoJSONEncoder

from .util import set_region, regions_data, available_regions
from .forms import RegionSelectionForm


@require_POST
def change_region(request, get_html_snippet=None):
    valid_regions = list(available_regions(request))
    region_form = RegionSelectionForm(request.POST,
                                      region_choices=valid_regions)

    if request.is_ajax():
        response = HttpResponse({}, content_type="application/json")
    else:
        next_url = request.POST.get('next')
        response = HttpResponseRedirect(next_url or
                                        request.META.get('HTTP_REFERER', '/'))

    if region_form.is_valid():
        success = set_region(request, response,
                             region_form.cleaned_data.get('region_id'))
    else:
        success = False

    if request.is_ajax():
        data = {
            "success": success,
            "regions": regions_data(request),
        }

        if get_html_snippet:
            data["html_snippet"] = get_html_snippet(request)

        response.content = json.dumps(data, cls=DjangoJSONEncoder)
    return response
