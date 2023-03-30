import json
from enum import Enum
from functools import wraps
from http import HTTPStatus
from urllib.parse import urlencode
from urllib.request import urlopen, Request

from authlib.integrations.flask_client import OAuth
from flask import request, Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from jose import jwt
from typing import Any, Union
from werkzeug import Response
from werkzeug.utils import redirect

from .exception import AuthError
from .management import setup_mgmt, get_user_by_email
from .misc import *
from .server_session import (profile_in_session, session_profile, session_clear,
                             set_session_value, set_profile_value,
                             get_profile_value, check_profile,
                             get_session_value, setup_session
                             )
from ..constants import \
    (PROFILE_KEY, JWT_PAYLOAD, AUTH0_DOMAIN, ALGORITHMS,
     AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_CALLBACK_URL, AUTH0_AUDIENCE,
     AUTH_MODE, Mode, DASHBOARD_URL, NEW_USER_QUERY,
     NEW_TEAM_QUERY, SET_TEAM_QUERY,
     LOGIN_URL, YES_ARG, AUTH_CONFIG_KEYS
     )
from ..models import (M_AUTH0_ID, M_ID, M_TEAM_ID, M_ROLE_ID, M_TEAM, M_NAME,
                      M_SURNAME, M_ROLE
                      )
from ..services import (get_user_by_auth0_id, is_unassigned_team,
                        is_manager_role, is_player_role, get_role_by_id,
                        get_team_by_id
                        )
from ..util import logger, fmt_log
from ..util.HTTPHeader import HTTPHeader

config = {k: "" if k != ALGORITHMS else [] for k in AUTH_CONFIG_KEYS}
auth0 = None

BEARER = "Bearer"
PERMISSIONS = "permissions"


class Conjunction(Enum):
    """
    Conjunction for permissions list.
    """
    AND = 1  # All listed permissions required.
    OR = 2  # Any one of listed permissions required.


class AuthErrorMode(Enum):
    """
    Authentication error handling mode.
    """
    EXCEPTION = 1  # Raise exception.
    REDIRECT = 2  # Redirect to login.


"""
Code in this module is based on 
https://auth0.com/docs/quickstart/backend/python#validate-access-tokens and 
https://github.com/auth0-samples/auth0-python-web-app/tree/master/01-Login
and course material
"""


# TODO get user info in AUTH_HEADER mode


def setup_auth(app: Flask, db: SQLAlchemy, no_sessions: bool = False):
    """
    Configure authentication.
    :param app: application
    :param db: A Flask-SQLAlchemy instance.
    :param no_sessions: disable server-side sessions
    """
    global config
    for key in AUTH_CONFIG_KEYS:
        if key not in app.config.keys():
            raise ValueError(f"{key} configuration not found")
        config[key] = app.config[key]

    auth0_base_url = f'https://{config[AUTH0_DOMAIN]}'
    set_auth0_base_url(auth0_base_url)

    setup_session(app, db, no_sessions=no_sessions)

    if AUTH_MODE == Mode.AUTHLIB:
        oauth = OAuth(app)

        global auth0
        auth0 = oauth.register(
            'auth0',
            client_id=config[AUTH0_CLIENT_ID],
            client_secret=config[AUTH0_CLIENT_SECRET],
            api_base_url=auth0_base_url,
            access_token_url=auth0_url('/oauth/token'),
            authorize_url=auth0_url('/authorize'),
            client_kwargs={
                'scope': 'openid profile email',
            },
            server_metadata_url=f'https://{config[AUTH0_DOMAIN]}/'
                                f'.well-known/openid-configuration'
        )

        setup_mgmt(config)


def role_is(role_id: int):
    """
    Check specified role is manager or player.
    :param role_id: role id to check
    :return: tuple of 'is manager', 'is player'
    """
    return is_manager_role(role_id), is_player_role(role_id)


def check_setup_complete(db_user: dict = None, auth0_user: dict = None):
    """
    Handle Auth0 callback in AUTHLIB mode
    :return:
    """
    # Get user details from auth0 & database.
    userinfo = get_jwt_payload()

    if auth0_user is None:
        auth0_user = get_user_by_email(userinfo[USERINFO_EMAIL])
    if db_user is None:
        db_user = get_user_by_auth0_id(get_profile_auth0_id())

    new_user = (db_user is None)
    if new_user:
        db_user = {
            M_ID: None,
            M_NAME: '',
            M_SURNAME: '',
            M_AUTH0_ID: '',
            M_ROLE_ID: 0,
            M_TEAM_ID: 0
        }
    role_id = db_user[M_ROLE_ID]
    is_manager, is_player = role_is(role_id)

    query = None
    if new_user or (auth0_user is not None and auth0_user['logins_count'] <= 1):
        # If its the user's first login or there is no entry in the database,
        # redirect to configure profile.
        query = NEW_USER_QUERY
    else:
        # If the user does not have a team, redirect to configure team.
        if is_unassigned_team(db_user[M_TEAM_ID]):
            if is_manager:
                # Managers need to create a team.
                query = NEW_TEAM_QUERY
            elif is_player:
                # Players need to set a team.
                query = SET_TEAM_QUERY
            else:
                raise ValueError(f'Unknown role is {role_id}')

    # Set setup complete flag in profile.
    set_profile_value(SETUP_COMPLETE, query is None)

    return query


def handle_login(access_token: str, userinfo: dict):
    """
    Handle Auth0 callback in AUTHLIB mode
    :return:
    """
    set_session_value(JWT_PAYLOAD, userinfo)

    def pick_if_db_user(db_value, other_value):
        return db_value if db_user[M_ID] is not None else other_value

    # Get user details from auth0 & database.
    auth0_user = get_user_by_email(userinfo[USERINFO_EMAIL])
    db_user = get_user_by_auth0_id(userinfo[USERINFO_SUB])
    if db_user is None:
        db_user = {
            M_ID: None,
            M_NAME: '',
            M_SURNAME: '',
            M_AUTH0_ID: '',
            M_ROLE_ID: 0,
            M_TEAM_ID: 0
        }

    # Set session profile.
    set_session_value(PROFILE_KEY, {
        M_AUTH0_ID: userinfo[USERINFO_SUB],
        USERINFO_PICTURE: userinfo[USERINFO_PICTURE],
        ACCESS_TOKEN: access_token,
    })
    set_profile_db_id(pick_if_db_user(db_user[M_ID], 0))
    set_profile_name(
        pick_if_db_user({
            M_NAME: db_user[M_NAME],
            M_SURNAME: db_user[M_SURNAME]
        }, {
            M_NAME: userinfo[USERINFO_NAME]
        })
    )
    set_profile_team({M_ID: pick_if_db_user(db_user[M_TEAM_ID], 0)})
    set_profile_role({M_ID: db_user[M_ROLE_ID]})

    query = check_setup_complete(db_user, auth0_user)
    location = DASHBOARD_URL \
        if query is None else f'{DASHBOARD_URL}?{query}={YES_ARG}'

    return redirect(location)


def callback_handling():
    """
    Handle Auth0 callback in AUTHLIB mode
    :return:
    """
    # Exchange Authorization Code for bearer token
    # https://auth0.com/docs/api/authentication?http#authorization-code-flow45
    auth0.authorize_access_token()
    # https://auth0.com/docs/api/authentication#get-user-info
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    return handle_login(auth0.token[ACCESS_TOKEN], userinfo)


def token_login_handling(access_token: str):
    """
    Handle login via an access token.
    :param access_token: token to use to login
    :return:
    """
    userinfo = get_userinfo(access_token)
    return handle_login(access_token, userinfo)


def is_logged_in():
    """
    Check if user is logged in.
    :return:
    """
    return profile_in_session()


def login():
    """
    Login in AUTHLIB mode.
    :return:
    """
    return auth0.authorize_redirect(redirect_uri=config[AUTH0_CALLBACK_URL],
                                    audience=config[AUTH0_AUDIENCE])


def logout():
    """
    Logout in AUTHLIB mode.
    :return:
    """
    session_clear()
    params = {'returnTo': url_for('home', _external=True),
              'client_id': config[AUTH0_CLIENT_ID]
              }
    return redirect(auth0_url(f'/v2/logout?{urlencode(params)}'))


def get_token_auth_header():
    """
    Get authorisation token from request header.
    :return: token
    :raise: AuthError
    """
    auth = request.headers.get(HTTPHeader.AUTHORIZATION, None)
    if auth is None:
        raise AuthError.auth_error(HTTPStatus.UNAUTHORIZED,
                                   'authorization_header_missing',
                                   'Authorization header is expected.')

    parts = auth.split()
    if len(parts) == 1:
        raise AuthError.auth_error(HTTPStatus.UNAUTHORIZED, 'invalid_header',
                                   'Token not found.')

    elif len(parts) > 2:
        raise AuthError.auth_error(HTTPStatus.UNAUTHORIZED, 'invalid_header',
                                   'Authorization header must be bearer token.')

    elif parts[0].lower() != BEARER.lower():
        raise AuthError.auth_error(HTTPStatus.UNAUTHORIZED, 'invalid_header',
                                   f'Authorization header must start with '
                                   f'"{BEARER}".')

    return parts[1]


def _check_payload(payload: dict):
    """
    Check for existence of permissions in JWT token payload.
    Note: Ensure RBAC is on in the Auth0 settings
    :param payload:     JWT token payload
    :return: True if payload ok
    """
    return payload is not None and PERMISSIONS in payload


def get_token_auth_client():
    """
    Get authorisation token from Authlib client.
    :return: token
    :raise: AuthError
    """
    # return auth0.token['access_token']
    return get_profile_value(ACCESS_TOKEN)


def get_profile():
    """
    Get the user's profile.
    :return: team id
    :raise: AuthError
    """
    return get_profile_value(PROFILE_KEY) if is_logged_in() else None


def get_profile_team_id():
    """
    Get the user's team id from profile.
    :return: team id
    :raise: AuthError
    """
    return get_profile_value(M_TEAM_ID)


def get_profile_setup_complete():
    """
    Get the user's profile setup status.
    :return: complete flag
    :raise: AuthError
    """
    return get_profile_value(SETUP_COMPLETE) if is_logged_in() else False


def get_profile_db_id():
    """
    Get the user's database id from profile.
    :return: db id
    :raise: AuthError
    """
    return get_profile_value(DB_ID)


def get_profile_auth0_id():
    """
    Get the user's auth0 id from profile.
    :return: auth0 id
    :raise: AuthError
    """
    return get_profile_value(M_AUTH0_ID)


def get_profile_role():
    """
    Get the user's role flags.
    :return: dict of manager and player flags
    :raise: AuthError
    """
    return get_profile_value('role_dict') if is_logged_in() else {
        k: False for k in [MANAGER_ROLE, PLAYER_ROLE]
    }


def get_profile_is_manager():
    """
    Get the user's manager flag.
    :return: bool
    :raise: AuthError
    """
    return get_profile_value(MANAGER_ROLE) if is_logged_in() else False


def get_profile_is_player():
    """
    Get the user's player flag.
    :return: bool
    :raise: AuthError
    """
    return get_profile_value(PLAYER_ROLE) if is_logged_in() else False


def get_profile_role_permissions():
    """
    Get the user's role permissions from profile.
    :return: dict of manager and player flags
    :raise: AuthError
    """
    return \
        get_profile_value(ROLE_PERMISSIONS) if profile_in_session() and \
        ROLE_PERMISSIONS in session_profile().keys() else None


def get_jwt_payload():
    """
    Get the JWT payload from profile.
    :return: JWT payload
    :raise: AuthError
    """
    return get_session_value(JWT_PAYLOAD)


def get_jwt_payload_updated_at():
    """
    Get the user's profile last update date/time.
    :return: update date/time
    :raise: AuthError
    """
    jwt_payload = get_jwt_payload()
    return jwt_payload[USERINFO_UPDATED_AT] \
        if jwt_payload is not None \
        and USERINFO_UPDATED_AT in jwt_payload.keys() \
        else None


def set_profile_db_id(value: int):
    """
    Set the user's database id in the profile.
    :param: value   db id
    :raise: AuthError
    """
    set_profile_value(DB_ID, value)


def set_profile_team(value: Union[int, str, dict]):
    """
    Set the user's team in the profile. Depending on argument may set team id
    and team name or just id or name.
    :param: value   team name or if dict
    :raise: AuthError
    """
    if isinstance(value, int):
        set_profile_value(M_TEAM_ID, value)
    elif isinstance(value, str):
        set_profile_value(M_TEAM, value)
    elif isinstance(value, dict):
        if M_ID in value.keys():
            set_profile_value(M_TEAM_ID, value[M_ID])

            team = get_team_by_id(value[M_ID])
            team = '' if team is None else team[M_NAME]
            set_profile_value(M_TEAM, team)

        elif M_NAME in value.keys():
            set_profile_value(M_TEAM, value[M_NAME])


def set_profile_role_permissions(value: Any):
    """
    Set the user's role permissions in the profile.
    :param: value   role permissions
    :raise: AuthError
    """
    set_profile_value(ROLE_PERMISSIONS, value)


def set_profile_role(value: Union[int, str, dict]):
    """
    Set the user's role in the profile. Depending on argument may set all role
    related profile attributes or just role id or name.
    :param: value   role
    :raise: AuthError
    """
    if isinstance(value, int):
        set_profile_value(M_ROLE_ID, value)
    elif isinstance(value, str):
        set_profile_value(M_ROLE, value)
    elif isinstance(value, dict):
        if M_ID in value.keys():
            set_profile_value(M_ROLE_ID, value[M_ID])

            is_manager, is_player = role_is(value[M_ID])
            set_profile_value(MANAGER_ROLE, is_manager)
            set_profile_value(PLAYER_ROLE, is_player)

            role = get_role_by_id(value[M_ID])
            role = '' if role is None else role[M_ROLE]
            set_profile_value(M_ROLE, role)

            # ROLE_PERMISSIONS is only used during the initial signup workflow,
            # and is set there as required.
            set_profile_value(ROLE_PERMISSIONS, [])

        elif M_ROLE in value.keys():
            set_profile_value(M_TEAM, value[M_ROLE])


def set_profile_name(value: Union[str, dict]):
    """
    Set the user's name in the profile. Depending on argument may set all
    name-related profile attributes or just the name.
    :param: value   role
    :raise: AuthError
    """
    if isinstance(value, str):
        for key in [M_NAME, FULLNAME]:
            set_profile_value(key, value)
    elif isinstance(value, dict):
        if M_NAME in value.keys():
            set_profile_value(M_NAME, value[M_NAME])

            if M_SURNAME in value.keys():
                set_profile_value(FULLNAME,
                                  f'{value[M_NAME]} {value[M_SURNAME]}')


def get_userinfo(access_token: str):
    """
    Get the user's auth0 profile.
    :param access_token: The Auth0 Access Token obtained during login.
    :return:
    """
    # https://auth0.com/docs/api/authentication#get-user-info
    response = urlopen(
        Request(auth0_url('userinfo'), headers={
            'Authorization': f'{BEARER} {access_token}'
        }))
    return json.loads(response.read())


def check_permission(permission: str, payload: dict,
                     role_permissions: list = None,
                     mode: AuthErrorMode = AuthErrorMode.REDIRECT):
    """
    Check for existence of permission in JWT token payload or role permissions.
    Note: Ensure RBAC is on in the Auth0 settings
    :param permission:  permission to check for
    :param payload:     JWT token payload
    :param role_permissions: list of permissions associated with role
    :param mode:        error handling mode
    :return: True if present
    :raise: AuthError
    """
    if not _check_payload(payload) and mode == AuthErrorMode.REDIRECT:
        return redirect(LOGIN_URL)

    if permission not in payload[PERMISSIONS]:
        msg = f"{permission} not in payload {payload[PERMISSIONS]}"
        raise_error = True

        if isinstance(role_permissions, list):
            raise_error = (permission not in role_permissions)
            if raise_error:
                msg = f"{msg} or role {role_permissions}"

        if raise_error:
            logger().warning(fmt_log(msg))
            raise AuthError.auth_error(HTTPStatus.UNAUTHORIZED, 'unauthorized',
                                       'Permission not found.')
    return True


def _check_permissions_list(permissions: list[str], req_permissions: list[str],
                            join: Conjunction = Conjunction.OR):
    """
    Check for existence of permission in permissions list.
    :param permissions: list of permissions assigned
    :param req_permissions: list of permissions to check for
    :param join:        conjunction of list of permissions
    :return: True if present
    :raise: AuthError
    """
    ok = len(req_permissions) == 0  # If nothing to check, return ok.
    if not ok:
        count = 0
        for permission in req_permissions:
            if permission in permissions:
                count = count + 1

        ok = len(permissions) == count if join == Conjunction.AND else count > 0

    return ok


def check_permissions(permissions: list[str], payload: dict,
                      join: Conjunction = Conjunction.OR,
                      role_permissions: list = None,
                      mode: AuthErrorMode = AuthErrorMode.REDIRECT):
    """
    Check for existence of permission in JWT token payload or role permissions.
    Note: Ensure RBAC is on in the Auth0 settings
    :param permissions: list of permissions to check for
    :param payload:     JWT token payload
    :param join:        conjunction of list of permissions
    :param role_permissions: list of permissions associated with role
    :param mode:        error handling mode
    :return: True if present
    :raise: AuthError
    """
    if not _check_payload(payload) and mode == AuthErrorMode.REDIRECT:
        return redirect(LOGIN_URL)

    ok = _check_permissions_list(payload[PERMISSIONS], permissions, join=join)
    if not ok:
        msg = f"{'OR' if join == Conjunction.OR else 'AND'} " \
              f"{permissions} not in payload {payload[PERMISSIONS]}"

        if isinstance(role_permissions, list):
            ok = _check_permissions_list(role_permissions, permissions,
                                         join=join)
            if not ok:
                msg = f"{msg} or role {role_permissions}"

    if not ok:
        logger().warning(fmt_log(msg))
        raise AuthError.auth_error(HTTPStatus.UNAUTHORIZED, 'unauthorized',
                                   'Permission not found.')
    return True


def verify_decode_jwt(token):
    response = urlopen(auth0_url('/.well-known/jwks.json'))
    jwks = json.loads(response.read())  # JSON Web Key Set

    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise AuthError.auth_error(HTTPStatus.UNAUTHORIZED, 'invalid_header',
                                   'Authorization malformed.')

    if 'kid' not in unverified_header:
        raise AuthError.auth_error(HTTPStatus.UNAUTHORIZED, 'invalid_header',
                                   'Authorization malformed.')

    rsa_key = None
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
            break

    if rsa_key is not None:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=config[ALGORITHMS],
                audience=config[AUTH0_AUDIENCE],
                issuer=f'{get_auth0_base_url()}/'  # Trailing '/' is necessary.
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError.auth_error(HTTPStatus.UNAUTHORIZED, 'token_expired',
                                       'Token expired.')

        except jwt.JWTClaimsError:
            raise AuthError.auth_error(HTTPStatus.UNAUTHORIZED,
                                       'invalid_claims',
                                       'Incorrect claims. '
                                       'Please check the audience and issuer.')
        except Exception:
            raise AuthError.auth_error(HTTPStatus.BAD_REQUEST, 'invalid_header',
                                       'Unable to parse authentication token.')

    raise AuthError.auth_error(HTTPStatus.BAD_REQUEST, 'invalid_header',
                               'Unable to find the appropriate key.')


def check_auth(permission: str = '', permissions=None,
               join: Conjunction = Conjunction.OR,
               mode: AuthErrorMode = AuthErrorMode.REDIRECT):
    """
    Check authorisation.
    If 'permission' is specified 'permissions' is ignored.
    :param permission:  required permission
    :param permissions: required list of permissions
    :param join:        conjunction of list of permissions
    :param mode:        error handling mode
    :return:
    """
    if permissions is None:
        permissions = []

    if not check_profile(raise_error=(mode == AuthErrorMode.EXCEPTION)):
        return redirect(LOGIN_URL)

    if AUTH_MODE == Mode.AUTHLIB:
        token = get_token_auth_client()
    else:
        token = get_token_auth_header()
    payload = verify_decode_jwt(token)

    # If the role permissions are in session profile, then check those
    # for permission as well, (this arises in the case of a new user)
    role_permissions = get_profile_role_permissions()

    if len(permission):
        check_permission(permission, payload,
                         role_permissions=role_permissions, mode=mode)
    else:
        check_permissions(permissions, payload, join=join,
                          role_permissions=role_permissions, mode=mode)

    return payload


def requires_auth(permission: str = '', permissions=None,
                  join: Conjunction = Conjunction.OR,
                  mode: AuthErrorMode = AuthErrorMode.REDIRECT):
    """
    Authorisation decorator.
    If 'permission' is specified 'permissions' is ignored.
    :param permission:  required permission
    :param permissions: required list of permissions
    :param join:        conjunction of list of permissions
    :param mode:        error handling mode
    :return:
    """
    if permissions is None:
        permissions = []

    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            payload = check_auth(
                permission=permission, permissions=permissions, join=join,
                mode=mode
            )
            # Return the result of the decorated function or the response
            # from check_auth.
            return payload if isinstance(payload, Response) \
                else f(payload, *args, **kwargs)

        return wrapper

    return requires_auth_decorator
