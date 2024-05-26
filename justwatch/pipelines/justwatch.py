import logging

from .base import BasePipeline
from datetime import datetime

logger = logging.getLogger(__name__)


class JustWatchV2Pipeline(BasePipeline):
    COLLECTION_NAME_ITEMS = 'justwatch_v2'
    COLLECTION_NAME_PACKAGE = 'package_v2'

    SAVE_LINK_ITEMS = 'https://scraper.flickzen.com/Scraper/justWatch/multiple'
    SAVE_LINK_PACKAGE = 'https://scraper.flickzen.com/Scraper/justWatch/package/multiple'

    LIST_ITEMS = set()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def close_spider(self, spider):
        self.loop.run_until_complete(
            self.async_push_item(
                url=self.SAVE_LINK_PACKAGE,
                cursor=self.db[self.COLLECTION_NAME_PACKAGE].aggregate([{'$project': {'_id': 0}}]),
                push_name="packages"
            )
        )
        self.loop.run_until_complete(
            self.async_push_item(
                url=self.SAVE_LINK_ITEMS,
                cursor=self.db[self.COLLECTION_NAME_ITEMS].aggregate([{'$project': {'_id': 0}}]),
                push_name="items"
            )
        )

        super().close_spider(spider)

    def process_item(self, item, spider):
        item = {k: self.check_list(v) for k, v in item.items()}
        item['updated'] = datetime.utcnow()
        if item.get('packageId'):
            self.db[self.COLLECTION_NAME_PACKAGE].update_one(
                {"packageId": item['packageId']},
                {"$set": item},
                upsert=True
            )
        elif item.get('imdb_id'):
            self.LIST_ITEMS.add(item['imdb_id'])
            self.db[self.COLLECTION_NAME_ITEMS].update_one(
                {
                    "imdb_id": item['imdb_id'],
                    "country": item['country'],
                    "language": item['language']
                },
                {"$set": item},
                upsert=True
            )
        super().process_item(item, spider)
