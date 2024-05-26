import time
import uuid
import logging
import asyncio

import pymongo
# import requests (add to pipfile)

from aioscrapy import signals

from typing import Any
import aiohttp
from datetime import datetime, date, timezone

from pydantic import BaseModel

from justwatch.cache import InMemoryRedis

from pymongo.results import UpdateResult

from aioscrapy.utils.project import get_project_settings
import json

logger = logging.getLogger(__name__)
settings = get_project_settings()

# def replaced with async def (ALL)


class BasePipeline:
    SECRET_KEY = settings['SECRET_KEY']
    HEADERS = {"content-type": "application/json", 'service-key': SECRET_KEY}
    MAX_ACTIVE_FUTURES = 100
    LOG_EVERY = 250

    def __init__(self, crawler, mongo_uri, mongo_db, collection_name):
        self.crawler = crawler
        self.mongo_uri: str = mongo_uri
        self.mongo_db: str = mongo_db
        self.collection_name: str = collection_name
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.cache = InMemoryRedis()
        self.collection_spiders = self.db['spiders']
        self.loop = asyncio.get_event_loop()
        self.detail = {
            '_id': str(uuid.uuid4()),
            'is_debug': settings['DEBUG'],
            'name': self.collection_name,
            'start': datetime.utcnow(),
            'check_items': 0,
            'new_items': 0,
            'updated_items': 0,
            'not_change': 0,
            'error_items': 0,
        }

    @classmethod
    async def from_crawler(cls, crawler):
        spider = cls(
            crawler=crawler,
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'movies'),
            collection_name=crawler.spidercls.name,
        )
        return spider

    async def open_spider(self, spider):

        self.collection_spiders.update_one(
            {"_id": self.detail['_id']},
            {"$set": self.detail},
            upsert=True
        )
        await self.cache.crete_or_update(self.collection_name, self.detail)     # added await
        logger.info(f"Spider id = {self.detail['_id']}")

    async def close_spider(self, spider):
        self.detail['end'] = datetime.utcnow()
        req = self.cache.read(f'{self.collection_name}_request') or {}
        self.collection_spiders.update_one(
            {"_id": self.detail['_id']},
            {"$set": {**self.detail, **req}},
            upsert=True
        )
        await self.cache.crete_or_update(self.collection_name, self.detail)     # added await
        self.client.close()
        self.cache.close()
        logger.info(f"Spider close id = {self.detail['_id']}")
        logger.info('Close all works')

    async def process_item(self, item, spider):
        self.detail['check_items'] += 1
        await self.cache.crete_or_update(self.collection_name, self.detail)     # added await
        return item

    async def async_send_request(self, session, url, item):
        try:
            async with session.post(
                    url,
                    data=json.dumps(item, default=self.json_serial),
            ) as response:
                if response.status >= 299:
                    logger.error(
                        f"Error response statu {response.status}\n"
                        f"response text {await response.text()}\n"
                    )
                return response
        except asyncio.TimeoutError:
            logger.error("Timeout error: " + url)

    async def async_push_item(self, url: str, cursor: Any, push_name: str = ""):
        total = 0
        async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            items = []
            for item in cursor:
                if item.get('updated'):
                    item['updated'] = int(item['updated'].timestamp())
                items.append(item)
                total += 1
                if len(items) % 100 == 0:
                    await self.async_send_request(session, url, items)
                    logger.info(f'Send to API {total} {push_name}')
                    items = []
            await self.async_send_request(session, url, items)
            logger.info(f'Send to API summary {total} {push_name}')

    @staticmethod
    async def json_serial(obj):
        if isinstance(obj, (datetime, date)):
            return obj.replace(tzinfo=timezone.utc).isoformat()
        raise TypeError("Type %s not serializable" % type(obj))

    @staticmethod
    async def check_list(value):
        return [j.dict() if isinstance(j, BaseModel) else j for j in value] if isinstance(value, list) else value

    async def check_result(self, result: UpdateResult):
        if result.upserted_id:
            self.detail['new_items'] += 1
        else:
            if result.modified_count > 0:
                self.detail['updated_items'] += 1
            else:
                self.detail['not_change'] += 1
