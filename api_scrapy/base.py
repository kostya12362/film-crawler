import os
import importlib
from typing import Type
from uuid import uuid4, UUID
from collections import OrderedDict

from aioscrapy import Spider
from aioscrapy.crawler import CrawlerProcess, Crawler
from aioscrapy.utils.project import get_project_settings

from .exceptions import SpiderNotFound, InstanceNotFound
from .settings import config


class ScraperManager:
    def __init__(self):
        self.settings = get_project_settings()
        self.instance: dict[UUID, Crawler] = {}
        self.spiders = self._load_all_spiders()
        self.log_dir: str = config.log_dir

    @staticmethod
    def _load_all_spiders() -> dict[str, Type[Spider] | Crawler | str]:
        spiders = dict()
        for root, _, files in os.walk(config.BASE_DIR):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    module_path = str(os.path.join(root, file))
                    module_name = os.path.relpath(module_path, config.BASE_DIR).replace(os.path.sep, '.')[:-3]
                    if 'api_scrapy' in module_name:
                        continue
                    try:
                        module = importlib.import_module(module_name)
                        for attr in dir(module):
                            obj = getattr(module, attr)
                            if isinstance(obj, type) and issubclass(obj, Spider) and obj.__module__ == module.__name__:
                                spiders[obj.name] = obj
                    except ImportError:
                        continue
        return spiders

    async def start_scraper(self, spider_name: str):
        spider_class = self.spiders.get(spider_name)
        if not spider_class:
            raise SpiderNotFound()
        instance_id = uuid4()
        settings = dict(self.settings)
        settings |= dict(spider_class.custom_settings)
        settings['LOG_FILE'] = self._get_log_file_path(spider_name, instance_id)
        process = CrawlerProcess(settings)
        crawler = process.create_crawler(spider_class, settings)
        process.crawl_soon(crawler)
        self.instance[instance_id] = crawler

        return {"status": "started", "id": instance_id}

    async def stop_scraper(self, instance_id: UUID):
        if instance_id not in self.instance:
            raise InstanceNotFound

        crawler = self.instance[instance_id]
        await crawler.stop()
        # del self.instance[instance_id]
        return {"status": "stopped", "id": instance_id}

    def get_active_scrapers(self):
        return [self.get_scraper(i) for i in list(self.instance.keys())]

    def _get_stats(self, instance_id: UUID) -> dict:
        if instance_id not in self.instance:
            return {"error": "Instance not found"}
        crawler = self.instance[instance_id]
        stats = crawler.stats.get_stats()
        stats = OrderedDict((k, v) for k, v in sorted(stats.items()))
        stats = self._structure_stats(stats)
        return stats

    @staticmethod
    def _structure_stats(stats: dict) -> dict[str, dict]:
        structured_stats = {}
        for key, value in stats.items():
            parts = key.split('/')
            d = structured_stats
            for part in parts[:-1]:
                if part not in d:
                    d[part] = {}
                d = d[part]
            d[parts[-1]] = value
        return structured_stats

    def _get_log_file_path(self, spider_name: str, instance_id: UUID) -> str:
        log_dir = os.path.join(self.log_dir, spider_name)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        filename = f"{str(instance_id)}.log"
        return os.path.join(log_dir, filename)

    def get_scraper(self, instance_id: UUID) -> dict:
        if instance_id not in self.instance:
            raise InstanceNotFound
        crawler: Crawler = self.instance.get(instance_id)
        if crawler.spider is None:
            return {"id": instance_id, "status": "pending"}
        data = {
            "id": instance_id,
            "spider_name": crawler.spider.name,
            "stats": self._get_stats(instance_id),
            "log": {
                "level": crawler.spider.settings.get('LOG_LEVEL'),
                "file": crawler.spider.settings.get('LOG_FILE'),
                'stdout': crawler.spider.settings.get('LOG_STDOUT')
            },
            'metric': crawler.spider.settings.get('METRIC_LOG_ARGS'),
        }
        return data


scraper_manager = ScraperManager()
