import json
import asyncio

from uuid import uuid4, UUID

from aioscrapy.crawler import CrawlerProcess, Crawler
from aioscrapy.utils.project import get_project_settings

from .utils.tools import load_all_spiders, get_log_file_path, structure_stats
from .exceptions import SpiderNotFound, InstanceNotFound
from .models import Spider, SpiderStatus


class ScraperManager:
    def __init__(self):
        self.settings = get_project_settings()
        self.instance: dict[UUID, Crawler] = {}
        self.spiders = load_all_spiders()
        self.db_lock = asyncio.Lock()

    async def start_scraper(
            self,
            spider_name: str,
            instance_count: int = 1,
            project: str = None
    ):
        spider_class = self.spiders.get(spider_name)
        if not spider_class:
            raise SpiderNotFound()
        result = []
        for _ in range(instance_count):
            instance_id = uuid4()
            settings = dict(self.settings)
            settings |= dict(spider_class.custom_settings)
            settings['LOG_FILE'] = get_log_file_path(spider_name, instance_id)
            process = CrawlerProcess(settings)
            crawler: Crawler = process.create_crawler(spider_class, settings)
            process.crawl_soon(crawler)
            self.instance[instance_id] = crawler
            # async with self.db_lock:
            await Spider.create(
                id=instance_id,
                name=spider_name,
                spider=json.dumps(self.get_scraper(instance_id, crawler)),
                project=project,
            )
            asyncio.create_task(self._periodic_update_stats(instance_id, crawler))  # noqa
            result.append({"id": instance_id})
        return result

    async def _periodic_update_stats(self, instance_id, crawler: Crawler, interval=5):
        while instance_id in self.instance and crawler.engine.running:
            # async with self.db_lock:
            await Spider.update(
                id=instance_id,
                spider=self.get_scraper(instance_id, crawler),
                status=SpiderStatus.RUNNING
            )
            await asyncio.sleep(interval)

            # async with self.db_lock:
            await Spider.update(
                id=instance_id,
                spider=self.get_scraper(instance_id, crawler),
                status=SpiderStatus.FINISHED
            )

    async def stop_scraper(self, instance_id: UUID):
        if instance_id not in self.instance:
            raise InstanceNotFound

        crawler = self.instance[instance_id]
        await crawler.stop()
        del self.instance[instance_id]
        return {"status": "stopped", "id": instance_id}

    async def get_active_scrapers(self):
        scrapers = []
        for instance in await Spider.objects.all().order_by('created_at'):
            if instance.id in self.instance:
                crawler = self.instance[instance.id]
                scrapers.append(self.get_scraper(instance.id, crawler, instance.project))
            else:
                scrapers.append(instance.spider)
        return scrapers

    @classmethod
    async def get_projects(cls):
        spiders = await Spider.objects.all()
        projects_dict = {}
        base_instance = {i: [] for i in map(lambda x: x.value.lower(), SpiderStatus)}
        for spider in spiders:
            project_name = spider.project if spider.project else "default"
            if project_name not in projects_dict:
                projects_dict[project_name] = {"spiders": {}}

            if spider.name not in projects_dict[project_name]["spiders"]:
                projects_dict[project_name]["spiders"][spider.name] = base_instance.copy()

            projects_dict[project_name]["spiders"][spider.name][spider.status.value.lower()].append(spider.spider)

        projects_list = []
        for project, data in projects_dict.items():
            item = {"project": project, "spiders": []}
            for spider, status in data["spiders"].items():
                item["spiders"].append({"spider_name": spider, "status": status})
            projects_list.append(item)
        return projects_list

    @staticmethod
    def _get_stats(crawler: Crawler) -> dict:
        stats = crawler.stats.get_stats()
        stats = structure_stats(stats)
        return stats

    def get_scraper(
            self,
            instance_id: UUID,
            crawler: Crawler,
            project: str = None
    ) -> dict:
        if crawler.spider is None:
            return {
                "id": str(instance_id),
            }
        data = {
            "id": str(instance_id),
            "project": project,
            "spider_name": crawler.spider.name,
            "stats": self._get_stats(crawler),
            "log": {
                "level": crawler.spider.settings.get('LOG_LEVEL'),
                "file": crawler.spider.settings.get('LOG_FILE'),
                'stdout': crawler.spider.settings.get('LOG_STDOUT')
            },
            'metric': crawler.spider.settings.get('METRIC_LOG_ARGS'),
        }
        return data


scraper_manager = ScraperManager()
