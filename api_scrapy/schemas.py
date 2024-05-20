import enum
import os
from uuid import UUID
from urllib.parse import urlparse

from pydantic import BaseModel, Field, model_validator
from typing import Optional
from aioscrapy.utils.log import logger

from .utils.api import request
from .settings import config


class Downloader(BaseModel):
    request_bytes: Optional[int] = 0
    request_count: Optional[int] = 0
    request_method_count: Optional[dict[str, int]] = Field(default_factory=dict)
    response_bytes: Optional[int] = 0
    response_count: Optional[int] = 0
    response_status_count: Optional[dict[int, int]] = Field(default_factory=dict)


class SchedulerEnqueued(BaseModel):
    memory: Optional[int]


class Scheduler(BaseModel):
    enqueued: Optional[SchedulerEnqueued]


class Stats(BaseModel):
    downloader: Optional[Downloader]
    elapsed_time_seconds: Optional[float] = None
    finish_reason: Optional[str] = None
    start_time: Optional[str] = None
    finish_time: Optional[str] = None
    item_scraped_count: Optional[int] = 0
    response_received_count: Optional[int] = 0
    scheduler: Optional[Scheduler]


LogLevelEnum = enum.Enum(
    'LogLevelEnum',
    [(i.upper(), i.upper(),) for i in logger.__slots__]
)


class Log(BaseModel):
    level: LogLevelEnum
    file: str
    stdout: bool

    class Config:
        use_enum_values = True

    @model_validator(mode="before")
    @classmethod
    def _validate_dict(cls, data: dict) -> dict:
        req = request()
        parsed_url = urlparse(str(req.url))
        base_url = f"{parsed_url.scheme}://{parsed_url.hostname}:{parsed_url.port}"
        data['file'] = os.path.join(base_url, config.LOG_API_PATH, data['file'])
        return data


class ScraperResponse(BaseModel):
    id: UUID
    spider_name: str
    stats: Stats
    log: Log
    metric: dict
