from http import HTTPStatus
from typing import Any

from flask import session as server_session

from .exception import AuthError
from ..constants import PROFILE_KEY, MANAGER_ROLE, PLAYER_ROLE
from .misc import PROFILE_KEYS
from ..util import logger

session = {}    # Default, server-side sessions disabled.


def setup_session(no_sessions: bool = False):
    """
    Initialise server-side session management.
    :param no_sessions: disable server-side sessions
    """
    global session
    if not no_sessions:
        session = server_session    # Enable server-side sessions
    else:
        logger().info("Server-side sessions disabled.")


def profile_in_session():
    """
    Check profile in session.
    :return: True if profile key in session
    """
    return PROFILE_KEY in session.keys() if session else False


def check_profile(raise_error: bool = True):
    """
    Check profile is in session.
    :param raise_error: raise error flag
    :return: True or False
    :raise: AuthError
    """

    ok = profile_in_session()
    if not ok and raise_error:
        raise AuthError.auth_error(
            HTTPStatus.UNAUTHORIZED, 'no_session_profile', 'Login required.')
    return ok


def session_profile():
    """
    Get profile from session.
    :return: profile
    """
    return session[PROFILE_KEY] if profile_in_session() else {}


def session_clear():
    """
    Clear the session.
    """
    session.clear()


def set_session_value(key: str, value: Any):
    """
    Set a value in the session.
    :param key: key for value
    :param value: value to set
    """
    session[key] = value


def get_session_value(key: str):
    """
    Get a value from the session.
    :param key: key for required value
    :return: value
    """
    return session[key] if key in session.keys() else None


def set_profile_value(key: str, value: Any):
    """
    Set a value in the user's profile.
    :param key: key for value
    :param value: value to set
    :raise: AuthError
    """
    check_profile()
    if key in PROFILE_KEYS:
        session_profile()[key] = value
    else:
        raise ValueError(f'Unexpected profile key: {key}')


def get_profile_value(key: str):
    """
    Get a value from the user's profile.
    :param key: key for required value
    :return: value
    :raise: AuthError
    """
    check_profile()
    if key in PROFILE_KEYS:
        value = session_profile()[key]
    elif key == PROFILE_KEY:
        value = session_profile()
    elif key == 'role_dict':
        value = {
            k: session_profile()[k] for k in [MANAGER_ROLE, PLAYER_ROLE]
        }
    else:
        raise ValueError(f'Unexpected profile key: {key}')
    return value




