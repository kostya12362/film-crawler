import asyncio
from datetime import datetime

import aioscrapy
from aioscrapy.http import Response
from aioscrapy import Spider, Request

from aioscrapy.utils.project import get_project_settings
import pymongo
import logging
import json
import base64

from resources.graphql import QueryControl

from resources.сonstants import Variables

# from justwatch.parser.justwatch.justwatch_parser_v3 import ParserJustwatch

logger = logging.getLogger(__name__)
settings = get_project_settings()


class JustwatchSpider(Spider):
    # region SpiderSettings
    name = 'justwatch_v3'

    # Control url and domains
    allow_domains = ['apis.justwatch.com']
    base_url = 'https://apis.justwatch.com/graphql'
    localization_url = 'https://apis.justwatch.com/content/locales/state?platform=web'

    custom_settings = dict(
        USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        DOWNLOAD_DELAY=0.2,  # Some settings have changed
        RANDOMIZE_DOWNLOAD_DELAY=True,
        CONCURRENT_REQUESTS=20,

        CONCURRENT_REQUESTS_PER_DOMAIN=40,  # Danger (test)
        SCHEDULER_FLUSH_ON_START=True,  # Test feature from aioscrapy example
        RETRY_HTTP_CODES=[429, 408, 504],

        LOG_LEVEL='INFO',
        LOG_STDOUT=True,
        EXTENSIONS={
            'aioscrapy.libs.extensions.metric.Metric': 0,
        },
        ITEM_PIPELINES={
            'aioscrapy.libs.pipelines.csv.CsvPipeline': 100,
            # ! If not working well, try to add justwatch pipelines from imdb_project
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

    # endregion

    def __init__(self, *args, **kwargs):
        super(JustwatchSpider, self).__init__(*args, **kwargs)
        skip = int(kwargs.get('skip', 0))
        limit = int(kwargs.get('limit', 1))
        logger.info(f'skip = {skip} limit = {limit}--------------------------------')
        self.db = pymongo.MongoClient(settings['MONGO_URI'])[settings.get('MONGO_DATABASE', 'movies')]
        self.imdb = self.db['imdb'].aggregate([
            {
                "$match": {
                    "title.title": {"$ne": None},
                    "title.ratings_summary_aggregate": {"$gt": 5.0},
                    "title.ratings_summary_vote_count": {"$gt": 400},
                    "title.release_date": {"$gt": datetime(year=1980, month=1, day=1)}
                },
            },
            {
                "$project": {
                    "id": 1,
                    "titleName": "$title.title",
                    "year": {
                        "$year": {
                            "$toDate": "$title.release_date"
                        }
                    }
                }
            },
            {
                "$sort": {"id": 1}
            },
            {
                "$skip": skip
            },
            {
                "$limit": limit
            }
        ])

        # self.imdb = []
        # with open('/Users/ostapenkokostya/work/upwork/imdb/xx.json', 'r') as file:
        #     self.imdb = [{
        #         "id": i['id'],
        #         "year": i['year'],
        #         "titleName": i['titleName']
        #     } for i in json.loads(file.read())
        #         # if i['id'] in ['tt0120903', ]
        #     ]
        #     self.imdb = self.imdb[:10]

    async def start_requests(self):
        yield aioscrapy.Request(
            url='https://apis.justwatch.com/content/locales/state?platform=web',
            method='GET',
        )

    def parse(self, response: Response, **kwargs):
        localization = [i['full_locale'] for i in json.loads(response.text)]
        response.meta['localization'] = localization
        yield self.get_packages_request(response)
        packages = dict()
        data = json.loads(response.text)['data']['packages']
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
        if len(response.meta.get('_localization', [])):
            response.meta['packages'] = packages
            yield self.get_packages_request(response, packages=packages)
        else:
            for package in packages.values():
                _id = package['iconUrl'].split('/')[2]
                package['iconUrl'] = f'https://www.justwatch.com/images/icon/{_id}/s100/icon.webp'
                yield aioscrapy.Request(
                    url=package['iconUrl'],
                    callback=self.get_package,
                    meta={'package': package},
                    dont_filter=True
                )
            for i in self.imdb:
                yield aioscrapy.Request(
                    url=self.base_url,
                    method='POST',
                    body=json.dumps({
                        # "query": QUERY_SEARCH_PAGES,
                        "query": QueryControl.query_search_pages(),
                        "variables": {  # constants
                            "country": "US",
                            "language": "en",
                            "first": 50,
                            "filter": {
                                "searchQuery": i['titleName']
                            }
                        }
                    }),
                    headers=self.headers,
                    callback=self.get_item_in_usa,  # Everything okay in here? or do I need create this method?
                    cookies={},
                    meta={
                        "localization": response.meta['localization'],
                        "packages": packages,
                        "item": i
                    },
                    dont_filter=True,
                )

    def get_packages_request(self, response: Response, packages: dict = None):
        localization = response.meta['localization']
        if response.meta.get('_localization') is not None:
            _localization = response.meta['_localization']
        else:
            _localization = localization
        yield aioscrapy.Request(
            url=self.base_url,
            method='POST',
            body=json.dumps({
                # "query": QUERY_GET_ALL_PACKAGES,
                "query": QueryControl.query_all_packages(),
                "variables": {  # constants
                    "iconFormat": "WEBP",
                    "iconProfile": "S100",
                    "platform": "WEB",
                    "packagesCountry": _localization[0].split('_')[1],
                    "monetizationTypes": []
                }
            }),
            headers=self.headers,
            callback=self.get_packages,  # Everything okay in here? or do I need create this method?
            meta={
                'localization': localization,
                "_localization": _localization[1:],
                'packages': packages
            },
            cookies={},
            dont_filter=True,
        )

        # TODO: rewrite ParserJustwatch

        async def get_item_in_usa(self, response):
            data = self.find_data(response)
            if isinstance(data[0], dict):
                variables = json.loads(response.request.body.decode('utf-8'))['variables']  # constants
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

        def get_all_localization(self, response):
            data = json.loads(response.text)['href_lang_tags']
            countries = [{
                "country": i['locale'].split('_')[1],
                "language": i['locale'].split('_')[0]
            } for i in data if i['locale'] != 'en_US']
            if len(countries) > 0:
                yield aioscrapy.Request(
                    url=self.base_url,
                    method='POST',
                    body=json.dumps({
                        "query": self.create_query(countries),
                        "variables": self.get_variables(countries, response.meta['justwatch_id'])  # constants
                    }),
                    headers=self.headers,
                    callback=self.get_other_localization,
                    cookies={},
                    meta={
                        'packages': response.meta['packages'],
                        "item": response.meta['item']
                    },
                    dont_filter=True,
                )

        def get_other_localization(self, response):
            data = self.find_data(response)

            if isinstance(data[0], tuple):
                variables = json.loads(response.request.body.decode('utf-8'))['variables']  # constants
                for i in data[0]:
                    item = ParserJustwatch(data=i[1], by_fild=data[1], country=variables[f'country{i[0]}'],
                                           language=variables[f'language{i[0]}'], response=response)

                    yield item.get_data
            else:
                logging.error("Error in get_other_localization")

        # for item in data:
        #     # item |= {'__csv__': {
        #     #     'filename': '/Users/ostapenkokostya/work/movies/app/test.csv',
        #     #     'filename': './test.csv',
        #     # }}

    @staticmethod
    def get_package(response):
        package = response.meta['package']
        package['image'] = base64.b64encode(response.body).decode('utf-8')
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

    # TODO: move to graphql.py (def)

    @staticmethod
    def create_query(countries: list[dict[str, str]]) -> str:
        args = ','.join([f"$country_{i}: Country!, $language_{i}: Language!" for i in range(len(countries))])
        query = '\n'.join([f'''_{i}:node(id: $nodeId) {{
            ...SuggestedTitle_{i}   # ?I need to change something there? 
        }}''' for i in range(len(countries))])
        fragments = '\n'.join([f'''
            fragment SuggestedOffer_{i} on Offer {{
                monetizationType
                presentationType
                currency
                retailPrice(language: $language_{i})
                package {{
                    id
                }}
                standardWebURL
             }}
            fragment SuggestedTitle_{i} on MovieOrShow {{
                id
                offers(country: $country_{i}, platform: WEB) {{
                    ...SuggestedOffer_{i}
                    }}
            }}''' for i in range(len(countries))])
        return f'''
            query GetSuggestedTitles({args}, $nodeId: ID!) {{   # ?I need to change something there? 
                {query}
            }}
            {fragments}
        '''

    @staticmethod
    def get_variables(countries: list[dict[str, str]], justwatch_id: str):
        variables = dict()  # constants?
        for i, v in enumerate(countries):
            variables |= {f"country_{i}": v['country'], f"language_{i}": v['language']}
        variables['nodeId'] = justwatch_id
        return variables


# For Test
if __name__ == "__main__":
    JustwatchSpider.start()
