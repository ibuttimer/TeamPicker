from http import HTTPStatus


class AppError(Exception):
    """
    AbortError Exception
    A standardized way to communicate app related exceptions
    """
    def __init__(self, status_code: HTTPStatus, error: str = None):
        self.error = error
        self.status_code = status_code


class AbortError(AppError):
    """
    AbortError Exception
    A standardized way to communicate request abort related exceptions
    """
    def __init__(self, status_code: HTTPStatus, error: str = None):
        super(AbortError, self).__init__(status_code, error)
