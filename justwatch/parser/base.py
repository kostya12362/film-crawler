import re
import json
from functools import reduce
from pydantic import BaseModel, PrivateAttr
from typing import Optional, List, Union
from aioscrapy.http import Response

# def replaced with async def (ALL)


class BaseParserModel(BaseModel):
    _data: Optional[dict] = PrivateAttr()
    _response: Optional[Union[Response | dict]] = PrivateAttr()

    def __init__(self, response: Optional[Union[Response | dict]] = None, **kwargs):
        if response:
            if isinstance(response, Response):
                try:
                    data = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
                    if data:
                        self._data = json.loads(data)['props']['pageProps']
                        self._data = data
                except ValueError:
                    pass
            self._response = response
            item = dict()
            for field in list(set(self.__fields__.keys()) - set(kwargs.keys())):
                item[field] = getattr(self, f"_{field}")
            super().__init__(**(item | kwargs))
        else:
            super().__init__(**kwargs)

    @staticmethod
    async def fields_format(field: str):
        """originalTitle -> original_title"""
        return '_'.join([i.lower() for i in re.sub(r"([A-Z])", r" \1", field).split()])

    @staticmethod
    async def deep_get(dictionary: dict, path: str):
        keys = path.strip().split('.')
        return reduce(lambda d, key: d[int(key)] if isinstance(d, list) else d.get(key) if d else None, keys,
                      dictionary)

    @staticmethod
    async def clear_text(text: str | List[str] | None):
        if isinstance(text, str):
            return re.sub(r'\s+', ' ', text).strip() or None
        elif isinstance(text, list):
            return re.sub(r'\s+', ' ', ' '.join(text)).strip() or None

    @staticmethod
    async def to_float(text: str):
        try:
            return float(''.join(re.findall(r'[0-9\.]', text or '')))
        except ValueError:
            pass

    @staticmethod
    async def to_int(text: str):
        _v = ''.join(re.findall(r'[0-9\.]', text or ''))
        if _v and _v.isdigit():
            return int(_v)

    @staticmethod
    async def interesting_list(text: str) -> List[float]:
        list_value = re.findall(r'[0-9,.]+', text or '')
        if list_value:
            val = list(map(lambda x: float(re.sub(r',', '', x or '')), list_value))
            if val:
                return val
        return [0, 0]

    @staticmethod
    async def get_id_from_href(text: str) -> str | None:
        if text:
            return re.split(r'\/|\?', text)[2]

    @property
    async def _json(self):
        return json.loads(self._response.text)['data']['title']

    @staticmethod
    async def video_url(video_url: str):
        _id = video_url.split('/')[3]
        return f'https://www.imdb.com/video/imdb/{_id}/imdb/embed'
