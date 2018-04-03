# -*- coding: utf-8 -*-

from django.utils.deprecation import MiddlewareMixin

from .util import \
    LOCATION_COOKIE_NAME, get_cookie, get_country_code, get_region_id


class RegionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        info = get_cookie(request)

        updated = False
        if not info.get('country_code'):
            info['country_code'] = get_country_code(request)
            updated = True

        if not info.get('region_id'):
            info['region_id'] = get_region_id(info.get('country_code'))
            updated = True

        # If country or region have been updated, chnage the cookie for this
        # request only to ensure the change is reflected for this page load,
        # and save the updated info against the request so we can set the
        # cookie in process_response.
        if updated:
            request.COOKIES[LOCATION_COOKIE_NAME] = info
            request.shoptools_region_info = info

    def process_response(self, request, response):
        if hasattr(request, 'shoptools_region_info'):
            response.set_cookie(LOCATION_COOKIE_NAME,
                                request.shoptools_region_info)
        return response
