import unittest
from http import HTTPStatus
from typing import Union, Any, Optional, List
from unittest.mock import patch

from misc import MatchParam, UserType
from team_picker import create_app, parse_app_args, INIT_DB_ARG_LONG
from team_picker.constants import *
from team_picker.models import M_ID, User, Role, Team, Match, MatchSelections
from test_data import EqualDataMixin, ROLES, UNASSIGNED_TEAM

NO_PERMISSIONS = {
    "permissions": []
}
PLAYER_PERMISSIONS = {
    "permissions": [
        GET_ROLE_PERMISSION,

        POST_USER_PERMISSION,
        GET_USER_PERMISSION,
        GET_OWN_USER_PERMISSION,
        PATCH_OWN_USER_PERMISSION,
        DELETE_OWN_USER_PERMISSION,

        GET_TEAM_PERMISSION,

        GET_MATCH_PERMISSION,
        PATCH_OWN_MATCH_PERMISSION,
    ]
}
MANAGER_PERMISSIONS = {
    "permissions": PLAYER_PERMISSIONS["permissions"] + [
        PATCH_USER_PERMISSION,
        DELETE_USER_PERMISSION,

        POST_TEAM_PERMISSION,
        PATCH_TEAM_PERMISSION,
        DELETE_TEAM_PERMISSION,

        POST_MATCH_PERMISSION,
        PATCH_MATCH_PERMISSION,
        DELETE_MATCH_PERMISSION,
    ]
}
PERMISSIONS_BY_ROLE = {
    MANAGER_ROLE: MANAGER_PERMISSIONS,
    PLAYER_ROLE: PLAYER_PERMISSIONS
}

PACKAGE_MODULE = 'team_picker.auth'
AUTH_PATH = f'{PACKAGE_MODULE}.auth'
SERVER_SESSION_PATH = f'{PACKAGE_MODULE}.server_session'
MANAGEMENT_PATH = f'{PACKAGE_MODULE}.management'
TOKEN_FUNC = "get_token_auth_client" if AUTH_MODE == Mode.AUTHLIB \
    else "get_token_auth_header"

GET_TOKEN = "get_token"
PROFILE_IN_SESSION = "profile_in_session"
VERIFY_DECODE_JWT = "verify_decode_jwt"
GET_MGMT_API_TOKEN = "get_mgmt_api_token"


class BaseTestCase(unittest.TestCase):
    """This is the base class for all test cases."""

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)

        # Mock functions.
        # NOTE: Need to patch where an object is looked up, which is not
        # necessarily the same place as where it is defined.
        # https://docs.python.org/3/library/unittest.mock.html#where-to-patch
        self.mock_patchers = {}
        patchers = [(GET_TOKEN, f'{AUTH_PATH}.{TOKEN_FUNC}')] + \
                   [(k, f'{SERVER_SESSION_PATH}.{k}')
                    for k in [PROFILE_IN_SESSION]] + \
                   [(k, f'{AUTH_PATH}.{k}')
                    for k in [VERIFY_DECODE_JWT]] + \
                   [(k, f'{MANAGEMENT_PATH}.{k}')
                    for k in [GET_MGMT_API_TOKEN]]

        for key, target in patchers:
            self.setup_patcher(key, target)

    def setup_patcher(self, key: str, target):
        self.mock_patchers.update({
            key: patch(target)
        })

    def setUp(self):
        # Start patching 'auth' functions.
        self.mocker = {
            k: v.start() for k, v in self.mock_patchers.items()
        }
        for mock in self.mocker.values():
            self.addCleanup(mock.stop)

        # Configure the mock return values.
        self.setup_mocks()

        """Define test variables and initialize app."""
        base_url = 'http://localhost:5000/'
        self.app, self.db = create_app(
            args=parse_app_args(
                f'--{INIT_DB_ARG_LONG}'.split()),
            test_config={
                SECRET_KEY: 'test',
                DEBUG: True,  # Debug mode; True or False.
                TESTING: True,  # Testing mode; True or False.
                # https://github.com/wtforms/flask-wtf/blob/main/docs/config.rst
                'WTF_CSRF_ENABLED': False,  # Disable all CSRF protection.

                DB_DIALECT: 'sqlite',
                DB_DATABASE: 'test.db',
                DB_INSTANCE_RELATIVE_CONFIG: True,

                AUTH0_DOMAIN: 'udacity-fsnd.auth0.com',
                ALGORITHMS: ['RS256'],
                AUTH0_AUDIENCE: 'dev',
                AUTH0_CLIENT_ID: 'clientid',
                AUTH0_CLIENT_SECRET: 'clientsecret',
                BASE_URL: base_url,
                AUTH0_CALLBACK_URL: f'{base_url}callback',
                AUTH0_LOGGED_OUT_URL: base_url,
                NON_INTERACTIVE_CLIENT_ID: 'm2m_app_id',
                NON_INTERACTIVE_CLIENT_SECRET: 'm2m_app_secret',
                TEAM_PLAYER_ROLE_ID: 'auth0_player_role_id',
                TEAM_MANAGER_ROLE_ID: 'auth0_manager_role_id'
            })
        self.app.testing = True
        self.client = self.app.test_client()

        # Bind the app to the current context.
        with self.app.app_context():
            self.assertEqual(0, self.db.session.query(User).count())
            self.assertEqual(len(ROLES), self.db.session.query(Role).count())
            self.assertEqual(1, self.db.session.query(Team).count())
            self.assertEqual(0, self.db.session.query(Match).count())
            self.assertEqual(0, self.db.session.query(MatchSelections).count())

            # Get pre-configured roles.
            for _, r in ROLES.items():
                role = self.db.session.query(Role) \
                    .filter(Role.role == r.role) \
                    .first()
                if role is None:
                    self.fail(f"Could not find {r.role} role")
                r.id = role.id

            # Get pre-configured teams.
            team = self.db.session.query(Team) \
                .filter(Team.name == UNASSIGNED_TEAM_NAME) \
                .first()
            if team is None:
                self.fail(f"Could not find {UNASSIGNED_TEAM_NAME} team")
            UNASSIGNED_TEAM.id = team.id

    def setup_mocks(self):
        # Configure the mock return values.
        self.mocker.get(GET_TOKEN).return_value = \
            "no token required as it's ignored"
        self.mocker.get(PROFILE_IN_SESSION).return_value = False
        self.mocker.get(VERIFY_DECODE_JWT).return_value = NO_PERMISSIONS
        self.mocker.get(GET_MGMT_API_TOKEN).return_value = \
            "no mgmt token required as it's ignored"

    def context_wrapper(self, func):
        """
        Wrapper to run function in app context
        :param func: function to run
        """
        with self.app.app_context():
            func()

    @staticmethod
    def get_permissions_and_role(user_type: UserType,
                                 role: str = '') -> tuple:
        """
        Set the mock token payload to match the specified UserTyre
        :param user_type: User type to match
        :param role: designated role for user (used during setup)
        """
        role_id = 0
        if user_type == UserType.MANAGER:
            jwt_permissions = MANAGER_PERMISSIONS
            role_id = ROLES[MANAGER_ROLE].id
            role = MANAGER_ROLE
        elif user_type == UserType.PLAYER:
            jwt_permissions = PLAYER_PERMISSIONS
            role_id = ROLES[PLAYER_ROLE].id
            role = PLAYER_ROLE
        elif user_type == UserType.PUBLIC:
            jwt_permissions = NO_PERMISSIONS
        else:
            jwt_permissions = None

        return jwt_permissions, role_id, role

    def set_permissions(self, user_type: UserType,
                        profile: dict = None,
                        role: str = '') -> Optional[List[str]]:
        """
        Set the mock token payload to match the specified UserTyre
        :param user_type: User type to match
        :param profile: entries to add to mock profile
        :param role: designated role for user (used during setup)
        """
        jwt_permissions, role_id, role = \
            BaseTestCase.get_permissions_and_role(user_type, role=role)

        self.mocker.get(PROFILE_IN_SESSION).return_value = \
            (jwt_permissions is not None)
        self.mocker.get(VERIFY_DECODE_JWT).return_value = jwt_permissions

        return jwt_permissions[
            "permissions"] if jwt_permissions is not None else None

    @staticmethod
    def has_permission(permissions: Optional[List[str]],
                       permission: str) -> Optional[bool]:
        """
        Check if the specified permissions contains the specified privilege.
        :param permissions: list of permissions
        :param permission:   privilege to search for
        :return
        """
        if permissions is None:
            has = None
        else:
            has = permission in permissions
        return has

    def tearDown(self):
        """
        Method called immediately after the test method has been called
        and the result recorded.
        """
        # Stop patching 'auth' functions.
        for v in self.mocker.values():
            v.stop()

    def assert_response_status_code(self, expect: HTTPStatus, status_code: int,
                                    msg=None):
        self.assertEqual(expect, status_code, msg=msg)

    def assert_ok(self, status_code: int, msg=None):
        self.assert_response_status_code(HTTPStatus.OK, status_code, msg=msg)

    def assert_created(self, status_code: int, msg=None):
        self.assert_response_status_code(HTTPStatus.CREATED, status_code,
                                         msg=msg)

    def assert_bad_request(self, status_code: int, msg=None):
        self.assert_response_status_code(HTTPStatus.BAD_REQUEST, status_code,
                                         msg=msg)

    def assert_unauthorized_request(self, status_code: int, msg=None):
        self.assert_response_status_code(HTTPStatus.UNAUTHORIZED, status_code,
                                         msg=msg)

    def assert_not_found(self, status_code: int, msg=None):
        self.assert_response_status_code(HTTPStatus.NOT_FOUND, status_code,
                                         msg=msg)

    def assert_found(self, status_code: int, msg=None):
        self.assert_response_status_code(HTTPStatus.FOUND, status_code,
                                         msg=msg)

    def assert_equal_data(self, expected: EqualDataMixin, actual: dict,
                          ignore: list = None, **kwargs):
        """
        Test item equality.
        :param expected:    expected value
        :param actual:      actual value
        :param ignore:      list of attributes to ignore
        """
        self.assertTrue(expected.equals(actual, ignore=ignore, **kwargs),
                        msg=f'{expected} != {actual}')

    def assert_equal_dict(self, expected: dict, actual: dict,
                          ignore: list = None):
        """
        Test dict equality.
        :param expected:    expected value
        :param actual:      actual value
        :param ignore:      list of attributes to ignore
        """
        if ignore is None:
            ignore = []
        self.assertTrue(isinstance(expected, dict),
                        msg=f'{expected} not a dict')
        self.assertTrue(isinstance(actual, dict), msg=f'{actual} not a dict')
        for k, v in expected.items():
            if k not in ignore:
                self.assertTrue(k in actual.keys(), msg=f'{k} not in {actual}')
                self.assertEqual(v, actual[k],
                                 msg=f'actual[{k}] not equal expected {v}')

    def assert_body_entry(self, resp_body: dict, key: str, *args,
                          value: Any = None, msg=None):
        """
        Check a success response
        :param resp_body:   response body
        :param key:         key for entry
        :param value:       expected value
        :param match:       match type to check
        :param msg:         assert error message
        """
        self.assertTrue(isinstance(resp_body, dict))

        self.assertTrue(key in resp_body.keys(), msg=msg)

        resp_value = resp_body[key]
        expected_value = value
        if MatchParam.CASE_INSENSITIVE in args:
            resp_value = resp_body[key].lower()
            expected_value = value.lower()
        elif MatchParam.TO_INT in args:
            resp_value = int(resp_value)

        if MatchParam.EQUAL in args:
            self.assertEqual(expected_value, resp_value, msg=msg)
        elif MatchParam.NOT_EQUAL in args:
            self.assertNotEqual(expected_value, resp_value, msg=msg)
        elif MatchParam.TRUE in args:
            self.assertTrue(resp_value, msg=msg)
        elif MatchParam.FALSE in args:
            self.assertFalse(resp_value, msg=msg)
        elif MatchParam.IN in args:
            self.assertIn(resp_value, expected_value,
                          msg=f'{value} not found in {resp_value}'
                              f'{f" for {msg}" if msg is not None else ""}')
        elif len(args) > 0 and MatchParam.IGNORE not in args:
            raise ValueError(f'MatchParam {args} not supported')

    def assert_success_response(self, resp_body: dict, msg=None):
        """
        Check a success response
        :param resp_body:   response body
        :param msg:         assert error message
        """
        self.assert_body_entry(resp_body, "success", MatchParam.TRUE, msg=msg)

    def assert_error_response(self, resp_body: dict,
                              status_code: Union[int, range],
                              message: str, *args, msg=None):
        """
        Check an error response
        :param resp_body:   response body
        :param status_code: expected status code or range within it should be
        :param message:     expected message
        :param msg:         assert error message
        :param args:        list of MatchParam
        """
        self.assert_body_entry(resp_body, "success", MatchParam.FALSE, msg=msg)

        param = (MatchParam.TO_INT, MatchParam.IN) \
            if isinstance(status_code, range) else (MatchParam.EQUAL,)
        self.assert_body_entry(resp_body, "error", *param,
                               value=status_code, msg=msg)

        self.assert_body_entry(resp_body, "message", *args,
                               value=message, msg=msg)
