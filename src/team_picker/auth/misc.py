from ..constants import (ACCESS_TOKEN, DB_ID, ROLE_PERMISSIONS, PLAYER_ROLE,
                         MANAGER_ROLE, FULLNAME, SETUP_COMPLETE
                         )
from ..models import M_AUTH0_ID, M_NAME, M_TEAM, M_TEAM_ID, M_ROLE_ID, M_ROLE

AUTH0_BASE_URL = ''

# Fields from the userinfo response
# https://auth0.com/docs/api/authentication#get-user-info
USERINFO_SUB = 'sub'
USERINFO_EMAIL = 'email'
USERINFO_NAME = 'name'
USERINFO_PICTURE = 'picture'
USERINFO_UPDATED_AT = 'updated_at'

# Session profile keys
PROFILE_KEYS = [M_AUTH0_ID, M_NAME, USERINFO_PICTURE, FULLNAME,
                ACCESS_TOKEN, DB_ID, SETUP_COMPLETE,
                M_TEAM_ID, M_TEAM,
                M_ROLE_ID, M_ROLE, MANAGER_ROLE, PLAYER_ROLE, ROLE_PERMISSIONS,
                ]


def set_auth0_base_url(url: str):
    global AUTH0_BASE_URL
    AUTH0_BASE_URL = url


def get_auth0_base_url():
    return AUTH0_BASE_URL


def auth0_url(path: str):
    return f'{AUTH0_BASE_URL}{"" if path.startswith("/") else "/"}{path}'


