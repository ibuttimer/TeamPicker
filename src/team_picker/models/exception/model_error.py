from http import HTTPStatus

from ...util.exception import AppError


class ModelError(AppError):
    """
    ModelError Exception
    A standardized way to communicate database model related exceptions
    """
    def __init__(self, status_code: HTTPStatus, error: str = None):
        super(ModelError, self).__init__(status_code, error)
