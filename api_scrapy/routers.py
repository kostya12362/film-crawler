import os.path
import aiofiles
import json
from uuid import UUID

from fastapi import APIRouter, Path
from fastapi.responses import StreamingResponse

from .exceptions import InstanceNotFound
from .models import Spider
from .schemas import (
    AllDetailSpiderResponse,
    BaseSpiderSchema,
    SpiderSchema,
    BaseInstanceSchema,
    ProjectGroupSpiderResponse
)
from .base import scraper_manager
from .settings import config

router = APIRouter()
CHUNK_SIZE = 1024 * 1024


@router.get('/spiders', response_model=list[BaseSpiderSchema])
async def get_spiders():
    return [BaseSpiderSchema(spider_name=i) for i in scraper_manager.spiders]


@router.post(
    '/spiders',
    response_model=list[BaseInstanceSchema],
    response_model_exclude_none=True
)
async def start_spiders(body: SpiderSchema):
    return await scraper_manager.start_scraper(
        spider_name=body.spider_name,
        project=body.project,
        instance_count=body.instance_count
    )


@router.delete("/spiders/{id}")
async def stop_spiders(instance_id: UUID = Path(alias='id')):
    result = await scraper_manager.stop_scraper(instance_id)
    return result


@router.get('/instances', response_model=list[AllDetailSpiderResponse])
async def get_active_scrapers():
    return await scraper_manager.get_active_scrapers()


@router.get('/instances/{id}', response_model=AllDetailSpiderResponse)
async def get_scraper(instance_id: UUID = Path(alias='id')):
    obj = await Spider.get_or_none(id=instance_id)
    if obj is None:
        raise InstanceNotFound()
    return json.loads(obj.spider)


@router.get('/projects', response_model=list[ProjectGroupSpiderResponse])
async def get_projects():
    return await scraper_manager.get_projects()


@router.get('/logs/{spider_name}/{id}.log')
async def get_logs(spider_name: str, instance_id: UUID = Path(alias='id')):
    path = os.path.join(config.log_dir, spider_name, f"{str(instance_id)}.log")

    async def iter_file():
        async with aiofiles.open(path, 'rb') as f:
            while chunk := await f.read(CHUNK_SIZE):
                yield chunk

    headers = {'Content-Disposition': f'inline; filename="{instance_id}"'}
    return StreamingResponse(iter_file(), headers=headers, media_type='text/plain')
