import json
import redis
from datetime import datetime
from aioscrapy.utils.project import get_project_settings

settings = get_project_settings()

# def replaced with async def (ALL)


async def value_json(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return await obj
    # Added await


class InMemoryRedis:
    REDIS_TTL = 10 * 24 * 3600

    def __init__(self) -> None:
        self.redis = redis.Redis(
            host=settings['REDIS_HOST'],
            password=settings['REDIS_PASSWORD'],
            port=settings['REDIS_PORT'],
            encoding="utf-8",
            db=settings['REDIS_DB'],
            decode_responses=True,
        )

    async def create(self, key: str, data: dict):
        if self.redis.get(key):
            raise ValueError
        return self.redis.set(key, json.dumps(data, default=value_json), ex=self.REDIS_TTL)

    async def read(self, key: str) -> dict | None:
        try:
            data = self.redis.get(key)
            return json.loads(data)
        except TypeError:
            pass

    async def update(self, key: str, data: dict) -> None:
        sec = self.redis.ttl(key)
        return self.redis.set(key, json.dumps(data, default=value_json), ex=sec)

    async def update_ttl(self, key: str, data: dict):
        return self.redis.set(key, json.dumps(data, default=value_json), ex=self.REDIS_TTL)

    async def crete_or_update(self, key, data: dict) -> tuple[dict, bool]:
        if self.read(key):
            await self.update_ttl(key, data)    # added await
            return data, False,
        await self.create(key, data)    # added await
        return data, True

    async def delete(self, key: str) -> None:
        if self.redis.get(key):
            await self.redis.delete(key)    # added await
        raise KeyError

    def close(self):
        self.redis.close()


__all__ = [
    'InMemoryRedis'
]
