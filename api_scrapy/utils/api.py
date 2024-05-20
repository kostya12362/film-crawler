from contextlib import contextmanager
from contextvars import ContextVar
from typing import (
    Any,
    AsyncIterator,
    ContextManager,
    Iterator,
    TypeVar,
)

from fastapi import Depends, FastAPI, Request, Response
from fastapi.routing import APIRoute, APIRouter
from fastapi.dependencies.utils import (
    get_parameterless_sub_dependant,
)

ParentT = TypeVar("ParentT", APIRouter, FastAPI)

T = TypeVar("T")

response_value: ContextVar[Response] = ContextVar("response_value")
request_value: ContextVar[Request] = ContextVar("request_value")


def response() -> Response:
    try:
        return response_value.get()
    except LookupError:
        raise RuntimeError("response context var must be set")


def request() -> Request:
    try:
        return request_value.get()
    except LookupError:
        raise RuntimeError("request context var must be set")


def _ctx_var_with_reset(var: ContextVar, value: Any) -> ContextManager[None]:
    token = var.set(value)

    @contextmanager
    def _reset_ctx() -> Iterator[None]:
        yield
        var.reset(token)

    return _reset_ctx()


async def _set_request_response(req: Request, res: Response) -> AsyncIterator[None]:
    with _ctx_var_with_reset(response_value, res):
        with _ctx_var_with_reset(request_value, req):
            yield


async def _marker() -> None:
    pass


def _update_route(route: APIRoute) -> None:
    if any(d.call is _marker for d in route.dependant.dependencies):
        return

    dependencies = [
        Depends(_marker),
        Depends(_set_request_response),
    ]
    route.dependencies.extend(dependencies)
    route.dependant.dependencies.extend(
        get_parameterless_sub_dependant(
            depends=d,
            path=route.path_format,
        )
        for d in dependencies
    )


def init_api(parent: ParentT) -> ParentT:
    for route in parent.routes:
        if isinstance(route, APIRoute):
            _update_route(route)

    return parent


__all__ = [
    'init_api',
    'request',
]
