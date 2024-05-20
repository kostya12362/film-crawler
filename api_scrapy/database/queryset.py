from typing import AsyncIterator, Callable, Any, Self
from functools import wraps
from sqlalchemy import and_, select, delete, func, exists, ScalarResult, text, desc
from fastapi_async_sqlalchemy import db  # provide access to a database session

from .types import MODEL


class QuerySet:
    def __init__(self, model_cls: MODEL):
        self._model: MODEL = model_cls
        self._query = None
        self._filters_keys: set = set()
        self._filters: list = []
        self._order_by = []
        self._limit = None
        self._offset = None
        # self._only_load = None
        # self._joins = []
        self._method_calls = []
        self._only_one = False
        self._select = True

    @staticmethod
    def track_calls(only_one: bool = False, is_select: bool = True):
        def decorator(function: Callable[..., Any]):
            @wraps(function)
            def sync_wrapper(self: Self, *args, **kwargs):
                if only_one is True:
                    self._only_one = True
                else:
                    ValueError(f"You must pass at least one argument {function.__name__}")
                if is_select is False:
                    self._select = False
                method_name = function.__name__
                self._method_calls.append(method_name)
                result = function(self, *args, **kwargs)
                return result

            return sync_wrapper

        return decorator

    def _build_query(self):
        if self._query is None:
            self._query = select(self._model)
            if self._filters:
                self._query = self._query.where(and_(*self._filters))
            # if self._joins:
            #     for join in self._joins:
            #         self._query = self._query.options(join)
            if self._order_by:
                self._query = self._query.order_by(*self._order_by)
            if self._limit is not None:
                self._query = self._query.limit(self._limit)
            if self._offset is not None:
                self._query = self._query.offset(self._offset)
        return self._query

    def _kwargs_to_binary_expression(self, key, value):
        attr, *ops = key.split('__')
        column = getattr(self._model, attr)
        if ops:
            operation = ops[0]
            return getattr(column, operation)(value)
        else:
            return column == value

    @track_calls()
    def filter(self, **kwargs):
        for key, value in kwargs.items():
            # Создаем уникальный ключ для каждого фильтра для проверки
            filter_key = f"{key}_{value}"
            if filter_key not in self._filters:
                binary_expression = self._kwargs_to_binary_expression(key, value)
                self._filters.append(binary_expression)
                # Добавляем ключ фильтра в список применённых фильтров
                self._filters_keys.add(filter_key)
        return self

    @track_calls()
    def all(self):
        """
        Execute the query and return all results.
        """
        return self

    @track_calls()
    def order_by(self, *args: str):
        for arg in args:
            if arg.startswith('-'):
                # If the field starts with '-', remove the '-' and add desc() to the field
                self._order_by.append(desc(getattr(self._model, arg[1:])))
            else:
                # Otherwise, just add a field to sort in ascending order
                self._order_by.append(getattr(self._model, arg))
        return self

    @track_calls(only_one=True)
    def count(self):
        self._query = select(func.count()).select_from(self._query.subquery())
        return self

    @track_calls(only_one=True)
    def exists(self):
        self._query = select(exists(self._build_query()))
        return self

    @track_calls(is_select=False, only_one=True)
    def delete(self):
        query = self._build_query()
        self._query = delete(self._model.__table__).where(query.whereclause)
        return self

    @track_calls(only_one=True)
    def get(self, **kwargs) -> MODEL:
        if not kwargs:
            raise ValueError("You must pass at least one argument")
        self.filter(**kwargs)
        self.limit(1)
        return self

    @track_calls()
    def limit(self, limit: int):
        self._query = self._build_query().limit(limit)
        return self

    @track_calls()
    def offset(self, offset: int):
        self._query = self._query.offset(offset)
        return self

    @track_calls(only_one=True)
    def first(self):
        self._order_by.insert(0, desc(self._model.id))
        # self._order_by.insert(0, self._model.id)  # Сортировка по ID или другому уникальному полю
        return self.limit(1)

    @track_calls(only_one=True)
    def last(self):
        self._order_by.insert(0, desc(self._model.id))  # Сортировка по ID или другому уникальному полю
        return self.limit(1)

    async def _extract(self) -> ScalarResult[MODEL] | MODEL | None:
        self._query = self._build_query()
        if self._select:
            self.results = await db.session.scalars(self._query)
            if self._only_one:
                _result = self.results.unique().one_or_none()
            else:
                _result = self.results.all()
        else:
            self.results = await db.session.execute(self._query)
            db.session.commit()
            _result = self.results.unique().one_or_none()
        return _result

    def __await__(self):
        return self._extract().__await__()

    async def __aiter__(self) -> AsyncIterator[MODEL]:
        for val in await self:
            yield val
