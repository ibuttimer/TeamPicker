from enum import Enum

"""
Configuration related
"""
# Environment related
APP_CONFIG_PATH = 'APP_CONFIG_PATH'
INST_REL_CONFIG = 'INST_REL_CONFIG'
DEBUG = 'DEBUG'
TESTING = 'TESTING'
LOG_LEVEL = 'LOG_LEVEL'

# Database related
DB_CONFIG_VAR_PREFIX = 'DB_'  # Prefix for all database configuration variables.
DB_DIALECT = f'{DB_CONFIG_VAR_PREFIX}DIALECT'
DB_DRIVER = f'{DB_CONFIG_VAR_PREFIX}DRIVER'
DB_USERNAME = f'{DB_CONFIG_VAR_PREFIX}USERNAME'
DB_PASSWORD = f'{DB_CONFIG_VAR_PREFIX}PASSWORD'
DB_HOST = f'{DB_CONFIG_VAR_PREFIX}HOST'
DB_PORT = f'{DB_CONFIG_VAR_PREFIX}PORT'
DB_DATABASE = f'{DB_CONFIG_VAR_PREFIX}DATABASE'
DB_INSTANCE_RELATIVE_CONFIG = f'{DB_CONFIG_VAR_PREFIX}INSTANCE_RELATIVE_CONFIG'

# Auth0 related
AUTH0_CLIENT_ID = 'AUTH0_CLIENT_ID'
AUTH0_CLIENT_SECRET = 'AUTH0_CLIENT_SECRET'
AUTH0_CALLBACK_URL = 'AUTH0_CALLBACK_URL'
AUTH0_DOMAIN = 'AUTH0_DOMAIN'
AUTH0_AUDIENCE = 'AUTH0_AUDIENCE'
NON_INTERACTIVE_CLIENT_ID = 'NON_INTERACTIVE_CLIENT_ID'
NON_INTERACTIVE_CLIENT_SECRET = 'NON_INTERACTIVE_CLIENT_SECRET'
SECRET_KEY = 'SECRET_KEY'
ALGORITHMS = 'ALGORITHMS'

TEAM_PLAYER_ROLE_ID = 'TEAM_PLAYER_ROLE_ID'
TEAM_MANAGER_ROLE_ID = 'TEAM_MANAGER_ROLE_ID'

ALL_CONFIG_VARIABLES = [
    APP_CONFIG_PATH, INST_REL_CONFIG, DEBUG, TESTING, LOG_LEVEL,
    DB_DIALECT, DB_DRIVER, DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT,
    DB_DATABASE, DB_INSTANCE_RELATIVE_CONFIG,
    AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_CALLBACK_URL, AUTH0_DOMAIN,
    AUTH0_AUDIENCE, NON_INTERACTIVE_CLIENT_ID, NON_INTERACTIVE_CLIENT_SECRET,
    SECRET_KEY, ALGORITHMS,
    TEAM_PLAYER_ROLE_ID, TEAM_MANAGER_ROLE_ID
]

# Request methods
GET = 'GET'
PATCH = 'PATCH'
POST = 'POST'
DELETE = 'DELETE'


# API routes related
API_URL = "/api"

ROLE_ID_PARAM = "role_id"
USER_ID_PARAM = "user_id"
TEAM_ID_PARAM = "team_id"
MATCH_ID_PARAM = "match_id"

ROLES_URL = f"{API_URL}/roles"
ROLE_BY_ID_URL = f"{ROLES_URL}/<int:{ROLE_ID_PARAM}>"
USERS_URL = f"{API_URL}/users"
USER_BY_ID_URL = f"{USERS_URL}/<int:{USER_ID_PARAM}>"
TEAMS_URL = f"{API_URL}/teams"
TEAM_BY_ID_URL = f"{TEAMS_URL}/<int:{TEAM_ID_PARAM}>"
MATCHES_URL = f"{API_URL}/matches"
NEW_MATCH_URL = f"{MATCHES_URL}/new"
MATCH_BY_ID_URL = f"{MATCHES_URL}/<int:{MATCH_ID_PARAM}>"

# UI routes related
HOME_URL = "/"
LOGIN_URL = "/login"
CALLBACK_URL = "/callback"
LOGOUT_URL = "/logout"
TOKEN_LOGIN_URL = f"{LOGIN_URL}/token"

DASHBOARD_URL = "/dashboard"
NEW_USER_QUERY = "new_user"
NEW_TEAM_QUERY = "new_team"
SET_TEAM_QUERY = "set_team"

USERS_UI_URL = "/users"
USER_SETUP_URL = f"{USERS_UI_URL}/setup"
USER_BY_ID_TEAM_URL = f"{USERS_UI_URL}/<int:{USER_ID_PARAM}>/team"

TEAMS_UI_URL = "/teams"
TEAM_SETUP_URL = f"{TEAMS_UI_URL}/setup"


MATCHES_UI_URL = "/matches"
NEW_QUERY = "new"
UPDATE_QUERY = "update"
SELECTIONS_QUERY = "selections"
SEARCH_QUERY = "search"
ORDER_QUERY = "order"
ORDER_DATE_ASC = "date_asc"
ORDER_DATE_DESC = "date_desc"

MATCH_BY_ID_UI_URL = f"{MATCHES_UI_URL}/<int:{MATCH_ID_PARAM}>"
SEARCH_MATCH_URL = f"{MATCHES_UI_URL}/search"
MATCH_SELECTIONS_UI_URL = f"{MATCH_BY_ID_UI_URL}/selections"
MATCH_USER_SELECTION_UI_URL = f"{MATCH_SELECTIONS_UI_URL}/<int:{USER_ID_PARAM}>"
SELECT_QUERY = "select"
TOGGLE_ARG = "t"
YES_ARG = "y"
NO_ARG = "n"
MAYBE_ARG = "m"
MATCH_CONFIRM_UI_URL = f"{MATCH_BY_ID_UI_URL}/confirm"
MATCH_USER_CONFIRM_UI_URL = f"{MATCH_CONFIRM_UI_URL}/<int:{USER_ID_PARAM}>"


TEAM = "team"
VENUE = "venue"
OPPOSITION = "opposition"
DATE_RANGE = "date_range"
TEAM_SCORE = "team_score"
OPPOSITION_SCORE = "opposition_score"

# Results related
RESULT_ONE_ROLE = "role"                # Single role result.
RESULT_LIST_ROLES = "roles"             # List of roles result.
RESULT_ONE_USER = "user"                # Single user result.
RESULT_LIST_USERS = "users"             # List of users result.
RESULT_ONE_TEAM = "team"                # Single team result.
RESULT_LIST_TEAMS = "teams"             # List of teams result.
RESULT_ONE_MATCH = "match"              # Single match result.
RESULT_LIST_MATCHES = "matches"         # List of matches result.
RESULT_CREATED_COUNT = "created"        # Created count result.
RESULT_UPDATED_COUNT = "updated"        # Updated count result.
RESULT_DELETED_COUNT = "deleted"        # Deleted count result.


# Permissions related.
GET_ROLE_PERMISSION = "get:role"
GET_USER_PERMISSION = "get:user"
POST_USER_PERMISSION = "post:user"
PATCH_USER_PERMISSION = "patch:user"
DELETE_USER_PERMISSION = "delete:user"
GET_OWN_USER_PERMISSION = "get:own-user"
PATCH_OWN_USER_PERMISSION = "patch:own-user"
DELETE_OWN_USER_PERMISSION = "delete:own-user"
GET_TEAM_PERMISSION = "get:team"
POST_TEAM_PERMISSION = "post:team"
PATCH_TEAM_PERMISSION = "patch:team"
DELETE_TEAM_PERMISSION = "delete:team"
GET_MATCH_PERMISSION = "get:match"
POST_MATCH_PERMISSION = "post:match"
PATCH_MATCH_PERMISSION = "patch:match"
DELETE_MATCH_PERMISSION = "delete:match"
PATCH_OWN_MATCH_PERMISSION = "patch:own-match"


# Session elements.
JWT_PAYLOAD = 'jwt_payload'
PROFILE_KEY = 'profile'
ACCESS_TOKEN = 'access_token'
DB_ID = 'db_id'
ROLE_PERMISSIONS = 'role_permissions'
FULLNAME = 'fullname'
SETUP_COMPLETE = 'setup_complete'


class Mode(Enum):
    AUTHLIB = 1         # Authlib client
    AUTH_HEADER = 2     # Bearer token in header


AUTH_MODE = Mode.AUTHLIB


# Pre-configured entities.
UNASSIGNED_TEAM_NAME = 'Unassigned'     # Name of unassigned team.
MANAGER_ROLE_NAME = 'Manager'           # Manager title.
PLAYER_ROLE_NAME = 'Player'             # Player title.
PRE_CONFIG_ROLE_NAMES = [MANAGER_ROLE_NAME, PLAYER_ROLE_NAME]

MANAGER_ROLE = 'manager'
PLAYER_ROLE = 'player'


APP_DATE_FMT = '%Y-%m-%d'
APP_TIME_FMT = '%H:%M'
APP_DATETIME_FMT = APP_DATE_FMT + ' ' + APP_TIME_FMT
