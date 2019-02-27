# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware

from googlesearch.user_agent import get_random_user_agent


class RotateUserAgentMiddleware(UserAgentMiddleware):
    def process_request(self, request, spider):
        request.headers.setdefault('User-Agent', get_random_user_agent())
