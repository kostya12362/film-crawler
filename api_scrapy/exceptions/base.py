import enum
from ..utils.tools import transform_upper_snake_case


class EnumException(enum.Enum):
    VALIDATION_ERROR = 'Validation error in the request body.', 422
    VALIDATION_QUERY_ERROR = 'Validation error in the request query.', 422

    SPIDER_NOT_FOUND = 'Not found spider', 404
    INSTANCE_NOT_FOUND = 'Instance not found', 404

    INVALID_AUTHORIZATION_CODE = "Invalid authorization code.", 403
    INVALID_JWT_TOKEN_EXPIRED = "Invalid token or expired token.", 403
    INVALID_AUTHENTICATION_SCHEME = "Invalid authentication scheme, {0} ", 403
    INVALID_API_KEY = "Invalid API key.", 403
    API_TOKEN_ALREADY_EXISTS = 'Token with this name already exists.', 400


class CustomException(Exception):
    def __init__(self, *args, exc_enum=None, headers=None):
        if exc_enum is None or not isinstance(exc_enum, EnumException):
            raise ValueError('Invalid exception type or not provided')
        self.message = exc_enum.value[0].format(*args)
        self.status_code = exc_enum.value[1]
        self.headers = headers
        self.code = transform_upper_snake_case(type(self).__name__)

    def __repr__(self):
        return f'{self.code}'

    def __str__(self):
        return self.code


class InvalidAuthorizationCode(CustomException):
    def __init__(self, *args):
        super().__init__(*args, exc_enum=EnumException.INVALID_AUTHORIZATION_CODE)


class InvalidApiKey(CustomException):
    def __init__(self, *args):
        super().__init__(*args, exc_enum=EnumException.INVALID_API_KEY)


class ApiTokenAlreadyExists(CustomException):
    def __init__(self, *args):
        super().__init__(*args, exc_enum=EnumException.API_TOKEN_ALREADY_EXISTS)


class SpiderNotFound(CustomException):
    def __init__(self, *args):
        super().__init__(*args, exc_enum=EnumException.SPIDER_NOT_FOUND)


class InstanceNotFound(CustomException):
    def __init__(self, *args):
        super().__init__(*args, exc_enum=EnumException.SPIDER_NOT_FOUND)
