# -*- coding: utf-8 -*-

from django.utils.deprecation import MiddlewareMixin

from .util import update_session


class RegionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        update_session(request)
