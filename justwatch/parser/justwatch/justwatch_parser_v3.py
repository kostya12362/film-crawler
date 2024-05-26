import json
from aioscrapy.http import Response
import re

# def replaced with async def (ALL)


async def extract_float(value_str: str) -> float | None:
    cleaned_str = re.sub(r'[^\d,\.]', '', value_str)
    cleaned_str = cleaned_str.replace(',', '.')
    try:
        return float(cleaned_str)
    except ValueError:
        return None


class ParserOffers:
    fields = [
        ('offer', 'offer'),
        ('presentationType', 'presentation_type'),
        # ('monetizationType', 'monetization_type'),
        ('retailPrice', 'retail_price'),
        ('currency', 'currency'),
        # ('lastChangeRetailPriceValue', 'last_change_retail_price_value'),
        ('standardWebURL', 'standard_web_url'),
        # ('deeplinkRoku', 'deeplink_roku'),
        # ('type', 'type'),
        ('package', 'package')
    ]

    def __init__(self, data: dict, packages: dict):
        self.data = data
        self.packages = packages

    @property
    async def offer(self):
        if self.data['monetizationType'].lower() == 'flatrate':
            return 'subscription'
        return self.data['monetizationType'].lower()

    @property
    async def presentation_type(self):
        return self.data['presentationType']

    @property
    async def monetization_type(self):
        return self.data['monetizationType']

    @property
    async def retail_price(self) -> float | None:
        if self.data.get('retailPrice'):
            return extract_float(self.data['retailPrice'])

    @property
    async def currency(self) -> str:
        return self.data['currency']

    @property
    async def last_change_retail_price_value(self):
        return self.data['lastChangeRetailPriceValue']

    @property
    async def standard_web_url(self):
        return self.data['standardWebURL']

    @property
    async def deeplink_roku(self):
        return self.data['deeplinkRoku']

    @property
    async def type(self):
        return self.data['type']

    @property
    async def package(self):
        return self.packages[self.data['package']['id']]['shortName']

    @property
    async def get_data(self) -> dict:
        data = dict()
        for i in self.fields:
            data[i[0]] = getattr(self, i[1])
        return data


class ParserJustwatch:
    fields = [
        ('imdb_id', 'imdb_id'),
        ('justwatch_id', 'justwatch_id'),
        ('offers', 'offers'),
        ('country', 'country'),
        ('language', 'language'),
        ('by_find', "by_find")
    ]

    def __init__(
            self,
            data: dict,
            by_fild: str,
            country: str,
            language: str,
            response: Response
    ):
        self.data = data
        self.by_fild = by_fild
        self.country = country
        self.language = language
        self.response = response
        # self.response = response
        # self.data, self.by_fild = self._data
        # self._variables = json.loads(self.response.request.body.decode('utf-8'))['variables']

    # @property
    # async def is_valid(self) -> bool:
    #     if not self.data or len(self.offers) == 0:
    #         return False
    #     return True

    # @property
    # async def country(self):
    #     return self.country
    #
    # @property
    # async def language(self):
    #     return self.language

    @property
    async def get_full_path(self) -> str | None:
        return self.data['content'].get('fullPath')

    # @property
    # async def _data(self) -> tuple[dict, str]:
    #     try:
    #         data = json.loads(self.response.text)['data']
    #         if data.get('node'):
    #             return data['node'], "node"
    #         elif data.get('popularTitles'):
    #             result = data['popularTitles']
    #             if result['edges']:
    #                 for i in result['edges']:
    #                     if i['node']['content']['externalIds']['imdbId'] == self.imdb_id:
    #                         return i['node'], "imdb_id"
    #                 for i in result['edges']:
    #                     if all((
    #                             i['node']['content']['title'] == self.response.meta['item']['titleName'],
    #                             i['node']['content']['originalReleaseYear'] == self.response.meta['item']['year']
    #                     )):
    #                         return i['node'], "date"
    #     except TypeError:
    #         pass
    #     return dict(), ""

    @property
    async def by_find(self) -> str:
        return self.by_fild

    @property
    async def offers(self) -> list:
        result = []
        for i in self.data['offers']:
            result.append(ParserOffers(data=i, packages=self.response.meta['packages']).get_data)
        return result

    @property
    async def imdb_id(self):
        return self.response.meta['item']['id']

    @property
    async def justwatch_id(self):
        return self.data['id']

    @property
    async def get_data(self) -> dict | None:
        data = dict()
        for i in self.fields:
            data[i[0]] = getattr(self, i[1])
        return data
