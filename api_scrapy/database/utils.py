from fastapi_async_sqlalchemy import db
from sqlalchemy.sql import update
from .base import Base
from ..models import Spider, SpiderStatus


async def create_tables():
    async with db():
        engine = db.session.bind
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        stmt = update(Spider).values(status=SpiderStatus.FINISHED).execution_options(synchronize_session="fetch")
        await db.session.execute(stmt)
        await db.session.commit()
    # await db.commit()
