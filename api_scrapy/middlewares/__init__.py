from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..middlewares.response_time import ResponseTimeMiddleware
from ..settings import config

from fastapi_async_sqlalchemy import SQLAlchemyMiddleware


def setup_middlewares(app: FastAPI):
    app.add_middleware(ResponseTimeMiddleware)
    app.add_middleware(SQLAlchemyMiddleware, db_url=config.get_db_uri)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
