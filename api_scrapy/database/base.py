from typing import (
    Type,
    Any,
)
from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncAttrs

from fastapi_async_sqlalchemy import db

from .queryset import QuerySet
from .metaclass import BaseMeta
from .types import MODEL

Base = declarative_base(metadata=MetaData(), metaclass=BaseMeta)


class Model(AsyncAttrs, Base):
    """Base database model."""
    __abstract__ = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def objects(self) -> 'QuerySet':
        return QuerySet(model_cls=self)

    def __str__(self):
        return f"<{self.__class__.__name__} {self.get_pk}>"

    def __repr__(self):
        pk = self.get_pk
        if isinstance(self.get_pk, str):
            return f"<{self.__class__.__name__}: {pk}>"
        return f"<{self.__class__.__name__}>"

    def __hash__(self):
        pk = self.get_pk
        if not pk:
            raise TypeError("Model instances without id are unhashable")
        return hash(pk)

    @property
    def get_pk(self):
        return getattr(self, 'id', None) or getattr(self, 'pk', None)

    @classmethod
    async def get_or_none(cls: Type[MODEL], **kwargs: Any) -> MODEL | None:
        obj = await cls.objects.get(**kwargs)
        if obj is None:
            return None
        return obj

    @classmethod
    async def create(cls: Type[MODEL], **kwargs) -> 'MODEL':
        instance = cls(**kwargs)
        async with db():  # Здесь происходит создание контекстного менеджера сессии
            db.session.add(instance)
            await db.session.commit()
            await db.session.refresh(instance)
        return instance

    @classmethod
    async def get_or_create(cls, defaults=None, **kwargs) -> tuple['MODEL', bool]:
        instance = await cls.get_or_none(**kwargs)
        created = False
        if instance is None:
            if defaults:
                kwargs.update(defaults)
            instance = await cls.create(**kwargs)
            created = True
        return instance, created

    @classmethod
    async def create_or_update(cls, defaults: dict = None, **kwargs: Any) -> tuple[MODEL, bool]:
        if defaults is None:
            defaults = {}
        instance = await cls.get_or_none(**kwargs)
        status = False
        async with db():  # Здесь происходит создание контекстного менеджера сессии
            if instance:
                for key, value in defaults.items():
                    setattr(instance, key, value)
                db.session.add(instance)
            else:
                params = {**kwargs, **defaults}
                instance = cls(**params)
                db.session.add(instance)
                status = True
            await db.session.commit()
            await db.session.refresh(instance)
        return instance, status

    @classmethod
    async def update(cls, id: Any, **kwargs) -> 'MODEL':
        async with db():  # Здесь происходит создание контекстного менеджера сессии
            instance = await db.session.get(cls, id)
            if instance:
                for key, value in kwargs.items():
                    setattr(instance, key, value)
                db.session.add(instance)
                await db.session.commit()
                await db.session.refresh(instance)
        return instance
