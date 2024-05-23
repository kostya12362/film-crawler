from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends

from .routers import router
from .utils.api import init_api
from .middlewares import setup_middlewares
from .security import APIKey
from .exceptions import exception_handler_setup

from .database.utils import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


class ScrapyAPI(FastAPI):

    def __init__(self, *args, **kwargs):
        kwargs['lifespan'] = lifespan
        super().__init__(*args, **kwargs)
        secret_key = kwargs.get('secret_key')
        setup_middlewares(self)
        exception_handler_setup(self)
        depends = [
            Depends(APIKey(secret_key=secret_key))
        ]
        self.include_router(router, dependencies=depends if secret_key else None, tags=['Spiders'])
        init_api(self)
