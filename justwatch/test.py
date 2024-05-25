import asyncio
from datetime import datetime

import aioscrapy
from aioscrapy.http import Response
from aioscrapy import Spider, Request

from aioscrapy.utils.project import get_project_settings
import pymongo
import logging
import json

# from pprint import pprint

logger = logging.getLogger(__name__)
settings = get_project_settings()


class JustWatchSpider(Spider):
    name = 'justwatch_test'

    # Control url and domains
    allow_domains = ['apis.justwatch.com']
    base_url = 'https://apis.justwatch.com/graphql'
    localization_url = 'https://apis.justwatch.com/content/locales/state?platform=web'

    custom_settings = dict(
        USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 "
                   "Safari/537.36",
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
        CLOSE_SPIDER_ON_IDLE=True,  # ? Which means (Google)
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

        # 'authority': 'api.coinmarketcap.com',
        # 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/'
        #           'webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',

    }

    #  !
    #  start_urls = [
    #     # 'https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing?start=1&limit=10000&'
    #     # 'sortBy=market_cap&sortType=desc&convert=USD&cryptoType=all&tagType=all&audited=false&'
    #     # 'aux=ath,atl,high24h,low24h,num_market_pairs,cmc_rank,date_added,'
    #     # 'max_supply,circulating_supply,total_supply,volume_7d,volume_30d,volume_60d,tags'
    # ]
    #

    handle_httpstatus_list = [400, 415, 422, 429, 502]

    def __init__(self, *args, **kwargs):
        super(JustWatchSpider, self).__init__(*args, **kwargs)
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

    # async def parse(self, response: Response):
    #     print(response.url)
    #     data = response.json()['data']['cryptoCurrencyList']
    #     result = [i['id'] for i in data]
    #     print(datetime.now().isoformat(), len(result))

    async def parse(self, response: Response, **kwargs):
        localization = [i['full_locale'] for i in json.loads(response.text)]
        response.meta['localization'] = localization
        yield self.get_packages_request(response)

    async def get_packages(self, response):
        packages = dict() if response.meta.get('packages') is None else response.meta['packages']
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
                        "query": QUERY_SEARCH_PAGES,
                        "variables": {
                            "country": "US",
                            "language": "en",
                            "first": 50,
                            "filter": {
                                "searchQuery": i['titleName']
                            }
                        }
                    }),
                    headers=self.headers,
                    callback=self.get_item_in_usa,
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
        return aioscrapy.Request(
            url=self.base_url,
            method='POST',
            body=json.dumps({
                "query": QUERY_GET_ALL_PACKAGES,
                "variables": {
                    "iconFormat": "WEBP",
                    "iconProfile": "S100",
                    "platform": "WEB",
                    "packagesCountry": _localization[0].split('_')[1],
                    "monetizationTypes": []
                }
            }),
            headers=self.headers,
            callback=self.get_packages,
            meta={
                'localization': localization,
                "_localization": _localization[1:],
                'packages': packages
            },
            cookies={},
            dont_filter=True,
        )


        # !!!!!!!!!!!


        # async def get_item_in_usa(self, response):
        #     data = self.find_data(response)
        #     if isinstance(data[0], dict):
        #         variables = json.loads(response.request.body.decode('utf-8'))['variables']
        #         data = ParserJustwatch(
        #             data=data[0],
        #             by_fild=data[1],
        #             country=variables['country'],
        #             language=variables['language'],
        #             response=response,
        #         )
        #         item = data.get_data
        #         if data.get_full_path and '/us/' in data.get_full_path:
        #             # Request extract all localization by full path
        #             yield aioscrapy.Request(
        #                 url=f"https://apis.justwatch.com/content/urls?path={data.get_full_path}",
        #                 headers=self.headers,
        #                 callback=self.get_all_localization,
        #                 meta={
        #                     'packages': response.meta['packages'],
        #                     'justwatch_id': item['justwatch_id'],
        #                     'item': response.meta['item'],
        #                 }
        #             )
        #         yield item

        # def get_all_localization(self, response):
        #     data = json.loads(response.text)['href_lang_tags']
        #     countries = [{
        #         "country": i['locale'].split('_')[1],
        #         "language": i['locale'].split('_')[0]
        #     } for i in data if i['locale'] != 'en_US']
        #     if len(countries) > 0:
        #         yield scrapy.Request(
        #             url=self.base_url,
        #             method='POST',
        #             body=json.dumps({
        #                 "query": self.create_query(countries),
        #                 "variables": self.get_variables(countries, response.meta['justwatch_id'])
        #             }),
        #             headers=self.headers,
        #             callback=self.get_other_localization,
        #             cookies={},
        #             meta={
        #                 'packages': response.meta['packages'],
        #                 "item": response.meta['item']
        #             },
        #             dont_filter=True,
        #         )
        #
        # def get_other_localization(self, response):
        #     data = self.find_data(response)
        #
        #     if isinstance(data[0], tuple):
        #         variables = json.loads(response.request.body.decode('utf-8'))['variables']
        #         for i in data[0]:
        #             item = ParserJustwatch(data=i[1], by_fild=data[1], country=variables[f'country{i[0]}'],
        #                                    language=variables[f'language{i[0]}'], response=response)
        #
        #             yield item.get_data
        #     else:
        #         logging.error("Error in get_other_localization")


        for item in data:
            # item |= {'__csv__': {
            #     'filename': '/Users/ostapenkokostya/work/movies/app/test.csv',
            #     'filename': './test.csv',
            # }}
            yield Request(
                url=f"https://api.coinmarketcap.com/data-api/v3/cryptocurrency/detail?id={item['id']}",
                headers=self.headers,
                callback=self.get_item,
                meta={'meta': item}
            )

    # From demo.py (test ver w/CMC
    async def get_item(self, response: Response):
        item = dict()
        item |= {'__csv__': {
            # 'filename': '/Users/ostapenkokostya/work/movies/app/test.csv',
            'filename': './test.csv',
        }}
        yield item
        # contracts = list()
        # # EXTRACT new cryptocurrency
        # data = json.loads(response.text)['data']
        # for fields in self.parser.FIELDS:
        #     item[fields] = getattr(self.parser(data=data), fields)
        # # EXTRACT contracts
        # if data.get('platforms'):
        #     for _c in data['platforms']:
        #         contract = dict()
        #         _p = self.parser_contract(data=data, contract=_c)
        #         for fields in self.parser_contract.FIELDS_CONTRACT:
        #             contract[fields[1]] = getattr(_p, fields[0])
        #         if _p.valid_contract:
        #             contracts.append(contract)
        #     item['contracts'] = contracts
        # yield item

    def get_packages_request(self, response):
        pass
