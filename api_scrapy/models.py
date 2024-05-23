import uuid
import enum

from sqlalchemy import orm, PickleType, Enum, select

from .database import Model, DateTimeMixin
from fastapi_async_sqlalchemy import db


class SpiderStatus(enum.Enum):  # noqa
    PENDING = 'PENDING'
    RUNNING = 'RUNNING'
    FINISHED = 'FINISHED'


class Spider(Model, DateTimeMixin):
    __tablename__ = 'spiders'
    id: orm.Mapped[uuid.UUID] = orm.mapped_column(primary_key=True, default=uuid.uuid4)
    name: orm.Mapped[str] = orm.mapped_column(nullable=False)
    status: orm.Mapped[str] = orm.mapped_column(
        Enum(SpiderStatus),
        nullable=False,
        default=SpiderStatus.PENDING,
    )
    project: orm.Mapped[str] = orm.mapped_column(default="default")
    spider: orm.Mapped[object] = orm.mapped_column(PickleType, nullable=False)
