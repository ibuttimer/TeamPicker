from .exception import __all__ as all_exception
from .auth import (setup_auth, callback_handling, login, logout, is_logged_in,
                   token_login_handling,
                   get_profile, get_profile_setup_complete,
                   get_profile_team_id, get_profile_role, get_profile_db_id,
                   get_profile_is_manager, get_profile_is_player,
                   get_profile_auth0_id, get_jwt_payload,
                   get_jwt_payload_updated_at,
                   set_profile_db_id, set_profile_team,
                   set_profile_role_permissions, set_profile_role,
                   set_profile_name,
                   check_auth, AuthErrorMode,
                   requires_auth, Conjunction, check_setup_complete
                   )
from .server_session import set_profile_value
from .management import add_user_role, get_role_permissions

__all__ = all_exception + [
    "setup_auth",
    "callback_handling,",
    "login",
    "logout",
    "is_logged_in",
    "get_profile",
    "get_profile_setup_complete",
    "get_profile_team_id",
    "get_profile_role",
    "get_profile_db_id",
    "get_profile_is_manager",
    "get_profile_is_player",
    "get_profile_auth0_id",
    "get_jwt_payload",
    "get_jwt_payload_updated_at",
    "set_profile_db_id",
    "set_profile_team",
    "set_profile_role_permissions",
    "set_profile_role,",
    "set_profile_name,",
    "check_auth",
    "AuthErrorMode",
    "requires_auth",
    "Conjunction",
    "check_setup_complete",

    "set_profile_value",

    "add_user_role",
    "get_role_permissions",
]
