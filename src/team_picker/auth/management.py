from typing import Optional, Any

from auth0.authentication import GetToken
from auth0.management import Auth0

from ..constants import (
    AUTH0_DOMAIN, NON_INTERACTIVE_CLIENT_ID, NON_INTERACTIVE_CLIENT_SECRET,
    TEAM_MANAGER_ROLE_ID, TEAM_PLAYER_ROLE_ID, MANAGER_ROLE, PLAYER_ROLE
    )
from .misc import auth0_url
from ..models import M_ID, M_ROLE
from ..services import get_role_by_role

mgmt_api_token: str = None

auth0_mgmt: Auth0 = None

config: dict = None


_ROLE_TITLES_ = [MANAGER_ROLE, PLAYER_ROLE]
_ROLES_ = {
    MANAGER_ROLE: TEAM_MANAGER_ROLE_ID,
    PLAYER_ROLE: TEAM_PLAYER_ROLE_ID
}


def setup_mgmt(cfg: dict):
    """
    Initialise the Auth0 management API.
    :param cfg: configuration
    """
    global config
    config = cfg

    global mgmt_api_token
    mgmt_api_token = get_mgmt_api_token()

    global auth0_mgmt
    auth0_mgmt = Auth0(config[AUTH0_DOMAIN], mgmt_api_token)


def get_user_by_email(email: str) -> Optional[dict]:
    """
    Get user details from the management api
    :param email: email of user to search for
    :return:
    """
    # https://auth0.com/docs/api/management/v2/#!/Users/get_users
    response = auth0_mgmt.users_by_email.search_users_by_email(email)

    # [{'created_at': '2021-05-25T15:53:25.531Z',
    # 'email': 'player1@teampicker.com', 'email_verified': False,
    # 'identities': [
    # {'connection': 'Username-Password-Authentication', 'provider': 'auth0', 'user_id': '60ad1d756620fa00699cd21d', 'isSocial': False}],
    # 'name': 'player1@teampicker.com',
    # 'nickname': 'player1',
    # 'picture': 'https://s.gravatar.com/avatar/5a274ba21302d79465e11027a298f0bf?s=480&r=pg&d=https%3A%2F%2Fcdn.auth0.com%2Favatars%2Fpl.png',
    # 'updated_at': '2021-05-25T17:33:55.526Z',
    # 'user_id': 'auth0|60ad1d756620fa00699cd21d',
    # 'last_password_reset': '2021-05-25T15:57:32.557Z',
    # 'last_ip': '84.203.35.30',
    # 'last_login': '2021-05-25T17:33:55.526Z',
    # 'logins_count': 6}]

    user = None
    if len(response) > 0:
        user = response[0]

    return user


def get_mgmt_api_token() -> str:
    """
    Handle Auth0 callback in AUTHLIB mode
    :return:
    """
    # https://github.com/auth0/auth0-python#management-sdk
    get_token = GetToken(
        config[AUTH0_DOMAIN], config[NON_INTERACTIVE_CLIENT_ID],
        client_secret=config[NON_INTERACTIVE_CLIENT_SECRET])
    token = get_token.client_credentials(
        auth0_url('/api/v2/')
    )
    return token['access_token']


def _get_auth0_role_id(role_id: str) -> tuple[Any, Any]:
    """
    Add a role to a user.
    :param role_id: database role id
    :return:
    """
    for role_title in _ROLE_TITLES_:
        role = get_role_by_role(role_title)
        if role[M_ID] == role_id:
            role_auth0_id = config[_ROLES_[role_title]]
            break
    else:
        raise ValueError(f'Unknown role id {role_id}')

    return role_auth0_id, role_title


def add_user_role(role_id: str, user_id: str) -> Optional[dict]:
    """
    Add a role to a user.
    :param role_id: database role id
    :param user_id: auth0 user id
    :return:
    """
    role_auth0_id, role_title = _get_auth0_role_id(role_id)

    # https://auth0.com/docs/api/management/v2#!/Users/post_user_roles
    response = auth0_mgmt.roles.add_users(role_auth0_id, [user_id])
    # No response content on success.
    response[M_ROLE] = role_title

    return response


def get_role_permissions(role_id: str) -> list[str]:
    """
    Add a role to a user.
    :param role_id: database role id
    :return:
    """
    role_auth0_id, role_title = _get_auth0_role_id(role_id)

    # https://auth0.com/docs/api/management/v2#!/Roles/get_role_permission
    response = auth0_mgmt.roles.list_permissions(role_auth0_id)

    return [n["permission_name"] for n in response["permissions"]]
