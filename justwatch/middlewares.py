import logging
import os
import aioscrapy
import random
import time
from aioscrapy.downloadermiddlewares.retry import RetryMiddleware
from aioscrapy.utils.response import response_status_message
from aioscrapy.utils.project import get_project_settings
from justwatch.cache import InMemoryRedis

logger = logging.getLogger(__name__)
settings = get_project_settings()


class TooManyRequestsRetryMiddleware(RetryMiddleware):
    PROXY_PORT = settings['SCRAPY_PROXY_PORT'] or 59100
    PROXY_USERNAME = settings['SCRAPY_PROXY_USERNAME']
    PROXY_PASSWORD = settings['SCRAPY_PROXY_PASSWORD']

    def __init__(self, crawler):
        super().__init__(crawler.settings)
        self.crawler = crawler
        self.name = self.crawler.spider.name
        self.cache_key = f'{self.name}_request'
        self.cache = InMemoryRedis()
        self.stats, _ = self.cache.crete_or_update(self.cache_key, {
            'count_request': 0,
            'count_request_retry': 0
        })

    @property
    def ips(self) -> list[str]:
        path = '/'.join(os.path.abspath(__file__).split('/')[:-1])
        with open(f'{path}/ips.txt') as file:
            data = file.read().split('\n')
        return data

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    @property
    def random_ip(self):
        proxy = random.choice(self.ips)
        self.stats['count_request'] += 1
        self.cache.crete_or_update(self.cache_key, self.stats)
        if proxy:
            return f'http://{self.PROXY_USERNAME}:{self.PROXY_PASSWORD}@{proxy}:{self.PROXY_PORT}'

    def process_request(self, request: scrapy.Request, spider):
        if 'https://scraper.flickzen.com' not in request.url:
            request.meta['proxy'] = self.random_ip

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        elif response.status == 429:
            self.crawler.engine.pause()
            request.meta['proxy'] = self.random_ip
            time.sleep(60)  # If the rate limit is renewed in a minute, put 60 seconds, and so on.
            logging.warning(f'Sleep 60 seconds')
            # add to redis cache
            self.stats['count_request_retry'] += 1
            self.cache.crete_or_update(self.cache_key, self.stats)

            self.crawler.engine.unpause()
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        elif response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response

        return response

    def process_exception(self, request, exception, spider):
        if exception:
            request.meta['proxy'] = self.random_ip
            return self._retry(request, exception, spider)
