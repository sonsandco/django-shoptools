# -*- coding: utf-8 -*-
import json

from django.utils.deprecation import MiddlewareMixin

from shoptools import settings as shoptools_settings
from .util import get_cookie, get_country_code, get_region_id, COOKIE_MAX_AGE


class RegionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        info = get_cookie(request)

        updated = False
        if not info.get('country_code'):
            country_code = get_country_code(request)
            if country_code:
                info["country_code"] = country_code
                updated = True

        if not info.get('region_id'):
            region_id = get_region_id(info.get('country_code'))
            if region_id:
                info["region_id"] = region_id
                updated = True

        # If country or region have been updated, change the cookie for this
        # request only to ensure the change is reflected for this page load,
        # and save the updated info against the request so we can set the
        # cookie in process_response.
        if updated:
            info = json.dumps(info)
            request.COOKIES[shoptools_settings.LOCATION_COOKIE_NAME] = info
            request.shoptools_region_info = info

    def process_response(self, request, response):
        if hasattr(request, 'shoptools_region_info'):
            response.set_cookie(shoptools_settings.LOCATION_COOKIE_NAME,
                                request.shoptools_region_info,
                                max_age=COOKIE_MAX_AGE, httponly=False)
        return response
