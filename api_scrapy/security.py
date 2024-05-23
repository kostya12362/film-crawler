from fastapi import Request
from fastapi.security import APIKeyHeader

from .exceptions import (
    InvalidAuthorizationCode,
    InvalidApiKey
)


class APIKey(APIKeyHeader):
    def __init__(self, secret_key: str, name: str = "x-api-key", auto_error: bool = True):
        super().__init__(name=name, auto_error=auto_error)
        self.secret_key = secret_key

    async def __call__(self, request: Request):
        credentials: str = await super().__call__(request)
        if credentials != self.secret_key:
            raise InvalidApiKey
        return credentials
