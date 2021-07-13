from http import HTTPStatus

from flask import session as server_session, Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from typing import Any

from .exception import AuthError
from .misc import PROFILE_KEYS
from ..constants import PROFILE_KEY, MANAGER_ROLE, PLAYER_ROLE, SESSION_TYPE, \
    FILESYSTEM_SESSION_TYPE, SQLALCHEMY_SESSION_TYPE, SESSION_TYPES
from ..util import logger

session = {}    # Default, server-side sessions disabled.


def setup_session(app: Flask, db: SQLAlchemy, no_sessions: bool = False):
    """
    Initialise server-side session management.
    :param app: application
    :param db: A Flask-SQLAlchemy instance.
    :param no_sessions: disable server-side sessions
    """
    global session
    if not no_sessions:

        app.config["SESSION_PERMANENT"] = True

        if SESSION_TYPE not in app.config.keys():
            app.config[SESSION_TYPE] = FILESYSTEM_SESSION_TYPE
        for key in SESSION_TYPES:
            setting = app.config[SESSION_TYPE].lower()
            if setting == key:
                app.config[SESSION_TYPE] = setting
                if setting == SQLALCHEMY_SESSION_TYPE:
                    app.config["SESSION_SQLALCHEMY"] = db
                break
        else:
            raise ValueError(f"{SESSION_TYPE} configuration not found")

        Session(app)

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




