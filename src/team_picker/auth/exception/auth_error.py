from http import HTTPStatus

"""
Code in this module is based on https://auth0.com/docs/quickstart/backend/python#validate-access-tokens
and course material
"""


class AuthError(Exception):
    """
    AuthError Exception
    A standardized way to communicate auth failure modes
    """
    def __init__(self, status_code: HTTPStatus, error: dict = None):
        self.error = error
        self.status_code = status_code

    @staticmethod
    def auth_error(status_code: HTTPStatus, code: str, description: str):
        return AuthError(status_code, {
            'code': code,
            'description': description
        })
