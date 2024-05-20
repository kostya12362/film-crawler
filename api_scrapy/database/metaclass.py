from typing import Any, Type
from sqlalchemy import orm, MetaData

from sqlalchemy.orm import DeclarativeMeta

from .types import MODEL
from .queryset import QuerySet

SCHEMA_DB: dict[str, MODEL] = {}


class BaseMeta(DeclarativeMeta):

    def __init__(cls, class_name: Any, bases: Any, dict_: Any, **kw: Any):
        meta_class: Type["MODEL.Meta"] = dict_.get("Meta", type("Meta", (), {}))
        _table_name = getattr(meta_class, "table", None)
        cls._fields = set()
        cls._relationships = set()
        cls._primary_keys = set()  # Добавление атрибута для хранения первичных ключей
        _table_name = getattr(meta_class, "table", None)
        _metadata = getattr(meta_class, "metadata", None)

        if _metadata:
            cls.metadata = _metadata

        if _table_name:
            cls.__tablename__ = _table_name
        cls._fields.union(cls._relationships)

        def __search_for_field_attributes(attrs: dict) -> None:
            for key, value in attrs.items():
                if isinstance(value, orm.properties.MappedColumn):
                    cls._fields.add(key)
                    if value.foreign_keys:
                        fk = list(value.foreign_keys)[0]._colspec
                        if isinstance(fk, str):
                            fields = fk.split(".")
                        else:
                            fields = fk.name.split(".")
                        # print(fields, cls.__tablename__, type(fields), key, 'xx' * 10)
                if isinstance(value, orm.properties.RelationshipProperty):
                    cls._relationships.add(key)

        __search_for_field_attributes(cls.__dict__)

        DeclarativeMeta.__init__(cls, class_name, bases, dict_, **kw)

    @property
    def objects(cls: Type["MODEL"]) -> "QuerySet[MODEL]":  # type: ignore
        return QuerySet(model_cls=cls)

    @property
    def get_pk(cls: Type["MODEL"]) -> str | set[str]:
        if len(cls.primary_keys) == 1:
            return cls.primary_keys.pop()
        return cls.primary_keys

    @property
    def primary_keys(cls: Type["MODEL"]) -> set[str]:
        return {
            key for key, value in cls.__dict__.items() if
            getattr(value, 'primary_key', False) and key.startswith('_') is False and key.endswith('_') is False
        }

    @property
    def fields(cls: Type["MODEL"]) -> set[str]:
        return cls._fields
