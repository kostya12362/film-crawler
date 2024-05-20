import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, async_scoped_session

from ..settings import config


class Database:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url, echo=True)
        self.SessionFactory = async_scoped_session(
            async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False),
            scopefunc=asyncio.current_task
        )

    async def get_session(self):
        return self.SessionFactory()


db = Database(config.get_db_uri)
