from fastapi import FastAPI, Depends

from .routers import router
from .utils.api import init_api
from .middlewares import setup_middlewares
from .security import APIKey
from .exceptions import exception_handler_setup


class ScrapyAPI(FastAPI):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.include_router(router, dependencies=[Depends(APIKey())])
        init_api(self)
        exception_handler_setup(self)
        setup_middlewares(self)
