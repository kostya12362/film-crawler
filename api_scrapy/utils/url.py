from typing import Optional, Mapping, Any
from urllib.parse import urlencode

from fastapi import Request
from starlette.requests import QueryParams


def params_to_base(query_params: QueryParams) -> bytes:
    flattened = []
    for key, value in query_params.multi_items():
        flattened.extend((key, entry) for entry in value.split(','))
    return urlencode(flattened, doseq=True).encode("utf-8")


def params_from_base(query_params: QueryParams) -> dict:
    query_dict = {}
    for key, value in query_params.multi_items():
        if query_dict.get(key):
            query_dict[key] += f",{value}"
        else:
            query_dict[key] = value
    return query_dict


def update_path(req: Request, to_update: Optional[Mapping[str, Any]] = None) -> str | None:
    url = req.url.replace_query_params(**params_from_base(req.query_params))
    if to_update is None:
        return None
    url = url.include_query_params(**to_update)
    return str(url)
