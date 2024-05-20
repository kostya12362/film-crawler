from typing import (
    Type,
    Any,
)
from sqlalchemy import BinaryExpression, MetaData, select, Select, and_
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
    def make_query(cls: Type[MODEL], **kwargs: Any) -> 'Select':
        """
        Создает SQL-запрос для модели на основе переданных фильтров.
        :param kwargs: Ключевые аргументы, которые используются для фильтрации результатов.
        :return: Объект Select, который представляет SQL-запрос.
        """
        query = select(cls)
        # Генерация фильтров на основе kwargs
        if kwargs:
            conditions = [cls._kwargs_to_binary_expression(**kwargs)]
            query = query.where(*conditions)
        return query

    @classmethod
    def _kwargs_to_binary_expression(cls: Type[MODEL], **kwargs: Any) -> BinaryExpression | None:
        expressions = [getattr(cls, key) == value for key, value in kwargs.items() if key in cls.__table__.columns]
        if expressions:
            return and_(*expressions)
        else:
            return None

    @classmethod
    async def get_or_none(cls: Type[MODEL], **kwargs: Any) -> MODEL | None:
        obj = await cls.objects.get(**kwargs)
        if obj is None:
            return None
        return obj

    @classmethod
    async def create(cls: Type[MODEL], **kwargs) -> 'MODEL':
        instance = cls(**kwargs)
        db.session.add(instance)
        await db.session.commit()
        await db.session.refresh(instance)
        return instance

    @classmethod
    async def get_or_create(cls, defaults=None, **kwargs) -> tuple['MODEL', bool]:
        """
        Get an object based on specified criteria or create a new one with specified attributes.
        :param defaults: A dictionary of values to initialize the object when it is created.
        :param kwargs: Object search criteria.
        :return: A tuple containing an object and a flag indicating whether the object was created (True) or
        found (False).
        """
        # Checking the presence of an object in the database
        instance = await cls.get_or_none(**kwargs)
        created = False
        if instance is None:
            # Object not found, create a new one
            if defaults:
                kwargs.update(defaults)
            print(kwargs)
            instance = await cls.create(**kwargs)
            # db.session.add(instance)
            created = True
            # await db.session.commit()
        return instance, created

    @classmethod
    async def create_or_update(cls, defaults: dict = None, **kwargs: Any) -> tuple[MODEL, bool]:
        if defaults is None:
            defaults = {}
        instance = await cls.get_or_none(**kwargs)
        status = False
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
