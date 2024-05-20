from fastapi import Request
from fastapi.security import APIKeyHeader

from .exceptions import (
    InvalidAuthorizationCode,
    InvalidApiKey
)

from .models import Token


class APIKey(APIKeyHeader):
    def __init__(self, name: str = "x-api-key", auto_error: bool = True):
        super().__init__(name=name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Token:
        credentials: str = await super().__call__(request)
        if credentials:
            # obj = await Token.objects.get(
            #     token=credentials,
            # )
            # if not obj:
            raise InvalidApiKey
            # return obj
        else:
            raise InvalidAuthorizationCode
