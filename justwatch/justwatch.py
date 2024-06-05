import json
import base64
import logging
from datetime import datetime

import asyncio

import aioscrapy
from aioscrapy import Spider, Request
from aioscrapy.http import Response
from aioscrapy.utils.project import get_project_settings

from resources.graphql import QueryControl
from parser.justwatch.justwatch_parser_v2 import ParserJustwatch

logger = logging.getLogger(__name__)
settings = get_project_settings()


class JustwatchSpider(Spider):
    name = 'justwatch_v3'
    graphql = QueryControl()

    # Control url and domains
    allow_domains = ['apis.justwatch.com']
    base_url = 'https://apis.justwatch.com/graphql'
    localization_url = 'https://apis.justwatch.com/content/locales/state?platform=web'

    custom_settings = dict(
        USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        DOWNLOAD_DELAY=0.2,
        RANDOMIZE_DOWNLOAD_DELAY=True,
        CONCURRENT_REQUESTS=20,

        CONCURRENT_REQUESTS_PER_DOMAIN=40,
        SCHEDULER_FLUSH_ON_START=True,
        RETRY_HTTP_CODES=[429, 408, 504],

        LOG_LEVEL='INFO',
        LOG_STDOUT=True,
        EXTENSIONS={
            'aioscrapy.libs.extensions.metric.Metric': 0,
        },
        ITEM_PIPELINES={
            'aioscrapy.libs.pipelines.csv.CsvPipeline': 100,
        },
        CLOSE_SPIDER_ON_IDLE=True,
        DOWNLOAD_HANDLERS_TYPE="httpx",
        HTTPX_CLIENT_SESSION_ARGS={'http2': True, 'follow_redirects': True, 'timeout': 10},
        HTTPERROR_ALLOW_ALL=True,
        METRIC_LOG_ARGS=dict(
            sink='./DemoMetricSpider.metric',
            rotation='20MB',
            retention=3
        ),
    )
    headers = {
        'authority': 'apis.justwatch.com',
        'accept': '*/*',
        'content-type': 'application/json',
        'origin': 'https://www.justwatch.com',
    }

    handle_httpstatus_list = [400, 415, 422, 429, 502]

    def __init__(self, *args, **kwargs):
        super(JustwatchSpider, self).__init__(*args, **kwargs)
        skip = int(kwargs.get('skip', 0))
        limit = int(kwargs.get('limit', 1))
        logger.info(f'skip = {skip} limit = {limit}--------------------------------')
        # Work with json
        self.imdb = []
        with open('Result_2.json', 'r') as file:
            self.imdb = [{
                "id": i['id'],
                "year": i['year'],
                "titleName": i['titleName']
            } for i in json.loads(file.read())
                if i['id'] in ['tt0120903', ]
            ]
            self.imdb = self.imdb[:10]

    async def start_requests(self):
        yield aioscrapy.Request(
            url='https://apis.justwatch.com/content/locales/state?platform=web',
            method='GET',
        )

    def parse(self, response: Response, **kwargs):
        localizations = [i['full_locale'] for i in json.loads(response.text)]
        print(localizations)
        #  Converting localizations to country
        for i in localizations[0:1]:
            # i = en_US, uk_UK, ru_RU, en_GB
            yield aioscrapy.Request(
                url=self.base_url,
                method='POST',
                body=self.graphql.get_package_body(i),
                headers=self.headers,
                callback=self.get_packages,
                cookies={},
                dont_filter=True,
            )
        # Search by imdb film title
        for i in self.imdb:
            # i = title
            yield aioscrapy.Request(
                url=self.base_url,
                method='POST',
                body=self.graphql.search_film(i),
                headers=self.headers,
                callback=self.get_item_in_usa,
                cookies={},
                dont_filter=True,
            )

    # Getting all packages
    async def get_packages(self, response: Response):
        data = json.loads(response.text)['data']['packages']
        packages = dict()
        for package in data:
            packages |= {
                package['id']: {
                    'packageId': package['packageId'],
                    'clearName': package['clearName'],
                    'shortName': package['shortName'],
                    'iconUrl': package['icon'],
                }
            }
            for addon in package['addons']:
                packages |= {
                    addon['id']: {
                        'packageId': addon['packageId'],
                        'clearName': addon['clearName'],
                        'shortName': addon['shortName'],
                        'iconUrl': addon['icon'],
                    }
                }
        # Print all received packages
        for i in packages.items():
            print(i)
        # Download icons
        for package_id, package in packages.items():
            _id = package['iconUrl'].split('/')[2]
            package['id'] = package_id
            package['iconUrl'] = f'https://www.justwatch.com/images/icon/{_id}/s100/icon.webp'
            yield aioscrapy.Request(
                url=package['iconUrl'],
                callback=self.get_package_image,
                meta={'package': package},
                dont_filter=True
            )

    # Search by en_US
    async def get_item_in_usa(self, response):
        data = self.find_data(response)
        if isinstance(data[0], dict):
            variables = json.loads(response.request.body.decode('utf-8'))['variables']
            data = ParserJustwatch(
                data=data[0],
                by_fild=data[1],
                country=variables['country'],
                language=variables['language'],
                response=response,
            )
            item = data.get_data
            if data.get_full_path and '/us/' in data.get_full_path:
                # Request extract all localization by full path
                yield aioscrapy.Request(
                    url=f"https://apis.justwatch.com/content/urls?path={data.get_full_path}",
                    headers=self.headers,
                    callback=self.get_all_localization,
                    meta={
                        'packages': response.meta['packages'],
                        'justwatch_id': item['justwatch_id'],
                        'item': response.meta['item'],
                    }
                )
                yield item
            else:
                logger.info(f"Not found item in get_item_in_usa {response.meta['item']['id']}")

    # Getting all localizations for the film
    def get_all_localization(self, response):
        data = json.loads(response.text)['href_lang_tags']
        countries = [{
            "country": i['locale'].split('_')[1],
            "language": i['locale'].split('_')[0]
        } for i in data if i['locale'] != 'en_US']
        if len(countries) > 0:
            justwatch_id = response.meta['justwatch_id']
            yield aioscrapy.Request(
                url=self.base_url,
                method='POST',
                body=self.graphql.get_all_localizations(countries, justwatch_id),
                headers=self.headers,
                callback=self.get_other_localization,
                cookies={},
                dont_filter=True,
            )

    def get_other_localization(self, response):
        data = self.find_data(response)
        if isinstance(data[0], tuple):
            variables = json.loads(response.request.body.decode('utf-8'))['variables']
            for i in data[0]:
                item = ParserJustwatch(data=i[1], by_fild=data[1], country=variables[f'country{i[0]}'],
                                       language=variables[f'language{i[0]}'], response=response)

                yield item.get_data
        else:
            logging.error("Error in get_other_localization")

    @staticmethod
    async def get_package_image(response: Response):
        package = response.meta['package']
        package['image'] = base64.b64encode(response.body).decode('utf-8')
        print(package)
        yield package

    @classmethod
    def find_data(cls, response: Response) -> tuple[dict | tuple[tuple[str, dict]] | None, str | None]:
        try:
            data = json.loads(response.text)['data']
            if data.get('popularTitles'):
                result = data['popularTitles']
                if result['edges']:
                    for i in result['edges']:
                        if i['node']['content']['externalIds']['imdbId'] == response.meta['item']['id']:
                            return i['node'], "imdb_id"
                    for i in result['edges']:
                        if all((
                                i['node']['content']['title'] == response.meta['item']['titleName'],
                                i['node']['content']['originalReleaseYear'] == response.meta['item']['year']
                        )):
                            return i['node'], "date"
            else:
                return tuple(data.items()), "node"
        except TypeError:
            pass
        return None, None


# For Test
if __name__ == "__main__":
    JustwatchSpider.start()
