import json
import os
from http import HTTPStatus

import argparse
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from typing import Any, Union

from .auth import (setup_auth, callback_handling, login, logout,
                   is_logged_in, get_profile_role, get_profile,
                   get_profile_setup_complete
                   )
from .auth.exception import AuthError
from .constants import (UNASSIGNED_TEAM_NAME, PRE_CONFIG_ROLE_NAMES,
                        DEBUG, TESTING, DB_INSTANCE_RELATIVE_CONFIG,
                        INIT_DB_ARG, POSTMAN_TEST_ARG, DB_URI, DB_URI_ENV_VAR,
                        DB_DRIVER, DB_USERNAME, DB_PASSWORD, GENERATE_API_ARG,
                        DB_HOST, DB_PORT, PERMANENT_SESSION_LIFETIME,
                        ALGORITHMS, INST_REL_CONFIG, APP_CONFIG_PATH,
                        ALL_CONFIG_VARIABLES, LOG_LEVEL, CMD_LINE_ARGS,
                        DB_CONFIG_VAR_PREFIX, API_URL,
                        HOME_URL, GET, PATCH, POST, DELETE,
                        DASHBOARD_URL, LOGIN_URL, CALLBACK_URL, LOGOUT_URL,
                        USER_SETUP_URL, USER_BY_ID_TEAM_URL, MATCHES_UI_URL,
                        MATCH_BY_ID_UI_URL, SEARCH_MATCH_URL,
                        MATCH_SELECTIONS_UI_URL, MATCH_USER_SELECTION_UI_URL,
                        MATCH_USER_CONFIRM_UI_URL, ROLES_URL, ROLE_BY_ID_URL,
                        USERS_URL, USER_BY_ID_URL, TEAMS_URL, TEAM_SETUP_URL,
                        TEAM_BY_ID_URL, MATCHES_URL, MATCH_BY_ID_URL,
                        TOKEN_LOGIN_URL)
from .controllers import (all_roles, get_role_by_id,
                          all_users, get_user_by_id, create_user,
                          delete_user, update_user, setup_user,
                          all_teams, get_team_by_id, create_team,
                          delete_team, update_team, setup_team_ui,
                          set_user_team,
                          all_matches_api, get_match_by_id_api,
                          create_match_api, delete_match_api,
                          update_match_api,
                          matches_ui, create_match_ui,
                          match_by_id_ui, delete_match_ui,
                          search_match_ui, match_selections,
                          match_user_selection, match_user_confirm,
                          home, dashboard, token_login
                          )
from .models import setup_db
from .models.exception import ModelError
from .util import (eval_environ_var_truthy, http_error_result,
                   set_logger, print_exc_info, logger,
                   eval_environ_var_none, DEFAULT_LOG_LEVEL, fmt_log
                   )
from .util.exception import AbortError

INIT_DB_ARG_LONG = "initdb"
INIT_DB_ARG_SHORT = "idb"
POSTMAN_TEST_ARG_LONG = "postman_test"
POSTMAN_TEST_ARG_SHORT = "pt"
GENERATE_API_ARG_LONG = "generate_api"
GENERATE_API_ARG_SHORT = "ga"

RESPONSE_HEADERS = [
    # CORS
    ('Access-Control-Allow-Headers', 'Content-Type,Authorization,true'),
    ('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS'),
    # No caching.
    ('Cache-Control', 'no-cache, no-store, must-revalidate'),   # HTTP 1.1.
    ('Pragma', 'no-cache'),   # HTTP 1.0.
    ('Expires', '0'),   # Proxies.
]


def convert_env_var(k):
    """
    Read and convert an environment variable.
    :param k: variable name
    :return:
    """
    value = os.environ.get(k)
    if k in [DEBUG, TESTING, DB_INSTANCE_RELATIVE_CONFIG,
             'SQLALCHEMY_TRACK_MODIFICATIONS',
             INIT_DB_ARG, POSTMAN_TEST_ARG]:
        # Convert boolean variables.
        value = eval_environ_var_truthy(k)
    elif k in [DB_URI, DB_URI_ENV_VAR, DB_DRIVER, DB_USERNAME,
               DB_PASSWORD, DB_HOST, GENERATE_API_ARG]:
        # Convert str or None variables.
        value = eval_environ_var_none(k)
        if k == DB_URI_ENV_VAR and value is not None:
            # Read value Database URL environment variable.
            value = eval_environ_var_none(value)
    elif k in [DB_PORT, PERMANENT_SESSION_LIFETIME]:
        # Convert integer variables.
        value = eval_environ_var_none(k)
        value = int(value) if value is not None else None
    elif k in [ALGORITHMS]:
        # Convert list of str variables.
        value = list(map(str.strip,
                         json.loads(value.replace("'", '"'))))
    return value


def create_app(args: argparse.Namespace, test_config=None) -> Flask:
    """
    Application factory.
    :param args:        command line arguments
    :param test_config: test configuration
    :return: application
    """
    # Create app
    inst_rel_config = False  # Default is absolute config path.
    if test_config is None:
        # Take environment variables from '.env', giving system environment
        # variables priority.
        load_dotenv(override=False)

        # Evaluate instance relative environment variable.
        inst_rel_config = eval_environ_var_truthy(INST_REL_CONFIG,
                                                  dflt_val=inst_rel_config)

    # Set absolute instance path to 'instance', as default location
    # moves depending on whether running app or testing.
    instance_path = os.path.realpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../",
                     "instance")
    )

    # ensure the instance folder exists
    os.makedirs(instance_path, exist_ok=True)

    app = Flask(__name__, instance_path=instance_path,
                instance_relative_config=inst_rel_config,
                static_url_path='/public', static_folder='./public'
                )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app_config_path = eval_environ_var_none(APP_CONFIG_PATH)
        if app_config_path is not None:
            # Load from an environment variable pointing to a configuration
            # file.
            app.config.from_envvar(APP_CONFIG_PATH, silent=False)
            config_mapping = None
        else:
            # Load from environment variables.
            config_mapping = {
                k: convert_env_var(k) for k in ALL_CONFIG_VARIABLES
            }
    else:
        # Load the test config.
        config_mapping = test_config

    if config_mapping is not None:
        app.config.from_mapping(config_mapping)

    set_logger(
        app, app.config.get(LOG_LEVEL, DEFAULT_LOG_LEVEL))

    logger().debug(fmt_log(f"Configuration: {app.config}"))

    # Process command line arguments.
    cmd_line_args = {k: False for k in CMD_LINE_ARGS}
    if isinstance(args, argparse.Namespace):
        # If script run using
        # "python src\team_picker\__init__.py --initdb --postman_test
        #  --generate_api api.md"
        cmd_line_args[INIT_DB_ARG] = args.initdb
        cmd_line_args[POSTMAN_TEST_ARG] = args.postman_test
        cmd_line_args[GENERATE_API_ARG] = args.generate_api
    elif isinstance(args, dict):
        # If run using
        # "set FLASK_APP=src.team_picker:create_app({
        #   "initdb":True, "postman_test:True, "generate_api":api.md
        #   })"
        for k, arg_list in [
            (INIT_DB_ARG, [INIT_DB_ARG_LONG, INIT_DB_ARG_SHORT]),
            (POSTMAN_TEST_ARG, [POSTMAN_TEST_ARG_LONG, POSTMAN_TEST_ARG_SHORT]),
            (GENERATE_API_ARG, [GENERATE_API_ARG_LONG, GENERATE_API_ARG_SHORT]),
        ]:
            cmd_line_args[k] = process_dict_arg(arg_list, args,
                                                dflt_val=cmd_line_args[k])

    # Environment variables have precedence over command line arguments.
    for k in CMD_LINE_ARGS:
        if k in os.environ:
            cmd_line_args[k] = config_mapping.get(k, cmd_line_args[k]) \
                if config_mapping is not None else convert_env_var(k)

    logger().debug(fmt_log(f"Command line: {cmd_line_args}"))

    if cmd_line_args[GENERATE_API_ARG]:
        # Make path to instance folder
        cmd_line_args[GENERATE_API_ARG] = \
            os.path.join(instance_path, cmd_line_args[GENERATE_API_ARG])

    # Setup database.
    with app.app_context():
        app_db = setup_db(app, {
            k: v for k, v in app.config.items()
            if k.startswith(DB_CONFIG_VAR_PREFIX)
        }, init=cmd_line_args[INIT_DB_ARG])

    # Setup authentication.
    # (Server-side sessions need to be disabled for Postman tests)
    setup_auth(app, app_db, no_sessions=cmd_line_args[POSTMAN_TEST_ARG])

    # CORS(app)
    cors = CORS(app, resources={
        rf"{API_URL}/*": {"origins": "*"},
    })

    # CORS Headers
    @app.after_request
    def after_request(response):
        for k, v in RESPONSE_HEADERS:
            response.headers.add(k, v)
        return response

    @app.context_processor
    def inject_globals():
        """
        Inject global variables into the template context.
        :return:
        """

        def print_in_console(message):
            # https://stackoverflow.com/a/42888467
            print(str(message))

        return {'logged_in': is_logged_in(),
                'setup_complete': get_profile_setup_complete(),
                'role': get_profile_role(), 'userinfo': get_profile(),
                'mdebug': print_in_console}

    # Routes
    new_file = True
    for endpoint_info in [
        # UI-related routes
        ("Home", "Home endpoint.",
         HOME_URL, home, [GET]),
        ("Dashboard", "Dashboard endpoint.",
         DASHBOARD_URL, dashboard, [GET]),
        ("Login", "Endpoint to handle login requests.",
         LOGIN_URL, login, [GET]),
        ("Callback", "Endpoint to handle Auth0 callback requests.",
         CALLBACK_URL, callback_handling, [GET]),
        ("Logout", "Endpoint to handle logout requests.",
         LOGOUT_URL, logout, [GET]),
        ("Setup user", "Endpoint to handle requests to set up a user.",
         USER_SETUP_URL, setup_user, [POST]),
        ("Set user's team", "Endpoint to handle requests to set a user's team.",
         USER_BY_ID_TEAM_URL, set_user_team, [POST]),
        ("Initialise match creation/search or list (UI)",
         "Endpoint to handle requests to start match creation or search, "
         "or list matches.",
         MATCHES_UI_URL, matches_ui, [GET]),
        ("Create a match (UI)",
         "Endpoint to handle requests to create/update a match.",
         MATCHES_UI_URL, create_match_ui, [POST]),
        ("Get/update a match (UI)",
         "Endpoint to handle requests to get/update a match.",
         MATCH_BY_ID_UI_URL, match_by_id_ui, [GET, PATCH, POST]),
        ("Search match (UI)",
         "Endpoint to handle match search requests.",
         SEARCH_MATCH_URL, search_match_ui, [POST]),
        ("Get match selections (UI)",
         "Endpoint to handle requests to get match selections.",
         MATCH_SELECTIONS_UI_URL, match_selections, [GET]),
        ("Update user match selection",
         "Endpoint to handle requests to update individual user's match "
         "selection status.",
         MATCH_USER_SELECTION_UI_URL, match_user_selection, [POST]),
        ("Update user match confirmation",
         "Endpoint to handle requests to update individual user's match "
         "confirmation status.",
         MATCH_USER_CONFIRM_UI_URL, match_user_confirm, [POST]),
        ("Delete match (UI)",
         "Endpoint to handle requests to DELETE match by id.",
         MATCH_BY_ID_UI_URL, delete_match_ui, [DELETE]),

        # API-related routes
        ("Get roles", "Endpoint to handle requests for all roles.",
         ROLES_URL, all_roles, [GET]),
        ("Get role by id", "Endpoint to handle requests for role by id.",
         ROLE_BY_ID_URL, get_role_by_id, [GET]),

        ("All users.", "Endpoint to handle requests for all users.",
         USERS_URL, all_users, [GET]),
        ("Create user", "Endpoint to handle requests to create a user.",
         USERS_URL, create_user, [POST]),

        ("Get user", "Endpoint to handle requests for user by id.",
         USER_BY_ID_URL, get_user_by_id, [GET]),
        ("Update user.", "Endpoint to handle requests to update user by id.",
         USER_BY_ID_URL, update_user, [PATCH]),
        ("Delete user", "Endpoint to handle requests to delete user by id.",
         USER_BY_ID_URL, delete_user, [DELETE]),

        ("All teams", "Endpoint to handle requests for all teams.",
         TEAMS_URL, all_teams, [GET]),
        ("Create team", "Endpoint to handle requests to create a team.",
         TEAMS_URL, create_team, [POST]),
        ("Setup team", "Endpoint to handle requests to set up a team.",
         TEAM_SETUP_URL, setup_team_ui, [POST]),
        ("Get team", "Endpoint to handle requests for team by id.",
         TEAM_BY_ID_URL, get_team_by_id, [GET]),
        ("Update team", "Endpoint to handle requests to update team by id.",
         TEAM_BY_ID_URL, update_team, [PATCH]),
        ("Delete team", "Endpoint to handle requests to delete team by id.",
         TEAM_BY_ID_URL, delete_team, [DELETE]),

        ("All matches", "Endpoint to handle requests for all matches.",
         MATCHES_URL, all_matches_api, [GET]),
        ("Create match", "Endpoint to handle requests to create a match.",
         MATCHES_URL, create_match_api, [POST]),
        ("Get match", "Endpoint to handle requests for match by id.",
         MATCH_BY_ID_URL, get_match_by_id_api, [GET]),
        ("Update match", "Endpoint to handle requests to PATCH match by id.",
         MATCH_BY_ID_URL, update_match_api, [PATCH]),
        ("Delete match", "Endpoint to handle requests to DELETE match by id.",
         MATCH_BY_ID_URL, delete_match_api, [DELETE]),
    ]:
        add_url_rule(app, endpoint_info,
                     generate_api=cmd_line_args[GENERATE_API_ARG],
                     new_file=new_file)
        new_file = False

    if cmd_line_args[POSTMAN_TEST_ARG]:
        add_url_rule(app,
                     ("Login (token)",
                      "Endpoint to handle login requests using an access "
                      "token (only for Postman testing).",
                      TOKEN_LOGIN_URL, token_login, [POST]),
                     generate_api=cmd_line_args[GENERATE_API_ARG],
                     new_file=new_file)

    # Error handlers
    @app.errorhandler(HTTPStatus.BAD_REQUEST)
    def bad_request(error):
        return http_error_result(HTTPStatus.BAD_REQUEST, error)

    @app.errorhandler(HTTPStatus.UNAUTHORIZED)
    def not_implemented(error):
        return http_error_result(HTTPStatus.UNAUTHORIZED, error)

    @app.errorhandler(HTTPStatus.NOT_FOUND)
    def not_found(error):
        return http_error_result(HTTPStatus.NOT_FOUND, error)

    @app.errorhandler(HTTPStatus.METHOD_NOT_ALLOWED)
    def method_not_allowed(error):
        return http_error_result(HTTPStatus.METHOD_NOT_ALLOWED, error)

    @app.errorhandler(HTTPStatus.UNPROCESSABLE_ENTITY)
    def unprocessable_entity(error):
        return http_error_result(HTTPStatus.UNPROCESSABLE_ENTITY, error)

    @app.errorhandler(HTTPStatus.NOT_IMPLEMENTED)
    def not_implemented(error):
        return http_error_result(HTTPStatus.NOT_IMPLEMENTED, error)

    @app.errorhandler(HTTPStatus.SERVICE_UNAVAILABLE)
    def service_unavailable(error):
        return http_error_result(HTTPStatus.SERVICE_UNAVAILABLE, error)

    @app.errorhandler(HTTPStatus.INTERNAL_SERVER_ERROR)
    def internal_server_error(error):
        return http_error_result(HTTPStatus.INTERNAL_SERVER_ERROR, error)

    @app.errorhandler(ValueError)
    def value_error(error):
        return http_error_result(HTTPStatus.INTERNAL_SERVER_ERROR, error)

    @app.errorhandler(AuthError)
    def handle_auth_error(error):
        return http_error_result(error.status_code, error)

    @app.errorhandler(ModelError)
    def value_error(error):
        return http_error_result(error.status_code, error)

    @app.errorhandler(AbortError)
    def value_error(error):
        return http_error_result(error.status_code, error)

    return app


def process_dict_arg(arg_list: list, args: dict, dflt_val=False) -> Any:
    """
    Process arguments from a dict.
    :param arg_list: list of argument options
    :param args: supplied application arguments
    :param dflt_val: default value
    :return: value
    """
    for arg in arg_list:
        if arg in args.keys():
            value = args[arg]
            break
    else:
        value = dflt_val
    return value


def add_url_rule(app, endpoint_info, generate_api: Union[bool, str] = False,
                 new_file=False):
    """
    Add a app route.
    :param app: Flask app
    :param endpoint_info: tuple of route info
    :param generate_api: filename for api doc generation, not generated if False
    :param new_file:
    """
    title, desc, endpoint, view_func, methods = endpoint_info

    if generate_api:
        if new_file:
            logger().info(fmt_log(f'Generating API documentation template at '
                          f'{generate_api}'))
            mode = "w"
        else:
            mode = "a"

        markdown = f"#### {title}\n{desc}\n\n" \
                   f"|                   | Description |\n" \
                   f"|------------------:|-------------|\n" \
                   f"| **Endpoint**      | `{endpoint}` |\n" \
                   f"| **Method**        | `{', '.join(methods)}` |\n" \
                   f"| **Query**         | - |\n" \
                   f"| **Request Body**  | - |\n" \
                   f"| **Data type**     | - |\n" \
                   f"| **Content-Type**  | - |\n" \
                   f"| **Response**      | 200: OK |\n" \
                   f"| **Response Body** | - |\n" \
                   f"| **Errors**        | 400: BAD REQUEST <br>" \
                   f" 401: UNAUTHORISED |\n" \
                   f"\n" \
                   f"For example,\n\n"

        for method in methods:
            markdown = f"{markdown}" \
                       f"*Request*\n\n{method} `{endpoint}`\n\n" \
                       f"*Response*\n\n" \
                       f"```json\n" \
                       f"{{\n" \
                       f"}}\n" \
                       f"```\n\n"

        with open(generate_api, mode, encoding='utf-8') as filehandle:
            filehandle.write(markdown)

    app.add_url_rule(endpoint, view_func=view_func, methods=methods)


def parse_app_args(argv: list) -> argparse.Namespace:
    """
    Parse arguments
    :param argv: command line arguments
    :return: argument namespace
    """
    # parse arguments
    parser = argparse.ArgumentParser(prog='TeamPicker')
    parser.add_argument(f"-{INIT_DB_ARG_SHORT}", f"--{INIT_DB_ARG_LONG}",
                        help="Initialise the database, default no",
                        action="store_true")
    parser.add_argument(f"-{POSTMAN_TEST_ARG_SHORT}",
                        f"--{POSTMAN_TEST_ARG_LONG}",
                        help="Disable server-side sessions, default no",
                        action="store_true")
    parser.add_argument(f"-{GENERATE_API_ARG_SHORT}",
                        f"--{GENERATE_API_ARG_LONG}",
                        help="Generate API Markdown documentation, "
                             "as specified file",
                        type=str)

    args = parser.parse_args(argv)
    return args
