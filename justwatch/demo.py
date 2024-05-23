import asyncio
from datetime import datetime
from aioscrapy.http import Response
from aioscrapy import Spider, Request


class JustwatchSpider(Spider):
    name = 'cmc1'
    custom_settings = dict(
        USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        DOWNLOAD_DELAY=0.5,
        RANDOMIZE_DOWNLOAD_DELAY=True,
        CONCURRENT_REQUESTS=12,
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
        'authority': 'api.coinmarketcap.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/'
                  'webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    }

    start_urls = [
        'https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing?start=1&limit=10000&'
        'sortBy=market_cap&sortType=desc&convert=USD&cryptoType=all&tagType=all&audited=false&'
        'aux=ath,atl,high24h,low24h,num_market_pairs,cmc_rank,date_added,'
        'max_supply,circulating_supply,total_supply,volume_7d,volume_30d,volume_60d,tags'
    ]

    async def parse(self, response: Response):
        print(response.url)
        data = response.json()['data']['cryptoCurrencyList']
        result = [i['id'] for i in data]
        print(datetime.now().isoformat(), len(result))

        for item in data:
            # item |= {'__csv__': {
            #     'filename': '/Users/ostapenkokostya/work/movies/app/test.csv',
            # }}
            yield Request(
                url=f"https://api.coinmarketcap.com/data-api/v3/cryptocurrency/detail?id={item['id']}",
                headers=self.headers,
                callback=self.get_item,
                meta={'meta': item}
            )

    async def get_item(self, response: Response):
        item = dict()
        item |= {'__csv__': {
            'filename': '/Users/ostapenkokostya/work/movies/app/test.csv',
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