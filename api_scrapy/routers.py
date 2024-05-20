import os.path
from uuid import UUID
import aiofiles

from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .schemas import ScraperResponse
from .base import scraper_manager
from .settings import config

router = APIRouter()
CHUNK_SIZE = 1024 * 1024


class SpiderSchema(BaseModel):
    spider_name: str


@router.get('/spiders', response_model=list[SpiderSchema])
async def get_spiders():
    return [SpiderSchema(spider_name=i) for i in scraper_manager.spiders]


@router.post('/spiders', response_model=dict)
async def start_scraper(body: SpiderSchema):
    result = await scraper_manager.start_scraper(body.spider_name)
    return scraper_manager.get_scraper(result['id'])


@router.delete("/spiders/{id}")
async def stop_scraper(instance_id: UUID = Path(alias='id')):
    result = await scraper_manager.stop_scraper(instance_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get('/instances', response_model=list[ScraperResponse])
def get_active_scrapers():
    return scraper_manager.get_active_scrapers()


@router.get('/instances/{id}', response_model=ScraperResponse)
async def get_scraper(instance_id: UUID = Path(alias='id')):
    return scraper_manager.get_scraper(instance_id)


@router.get(config.LOG_API_PATH + '/{spider_name}/{file}')
async def get_logs(spider_name: str, file: str):
    path = os.path.join(config.log_dir, spider_name, file)

    async def iter_file():
        async with aiofiles.open(path, 'rb') as f:
            while chunk := await f.read(CHUNK_SIZE):
                yield chunk

    headers = {'Content-Disposition': f'inline; filename="{file}"'}
    return StreamingResponse(iter_file(), headers=headers, media_type='text/plain')
