import json
import unittest
from copy import deepcopy
from enum import Enum
from http import HTTPStatus
from typing import Union

from flask import Response

from team_picker.constants import (USERS_URL, USER_BY_ID_URL,
                                   RESULT_ONE_USER, RESULT_LIST_USERS,
                                   RESULT_CREATED_COUNT,
                                   RESULT_DELETED_COUNT, RESULT_UPDATED_COUNT,
                                   POST_USER_PERMISSION, GET_USER_PERMISSION,
                                   DELETE_USER_PERMISSION,
                                   DELETE_OWN_USER_PERMISSION,
                                   PATCH_USER_PERMISSION,
                                   PATCH_OWN_USER_PERMISSION,
                                   )
from team_picker.models import (M_ID, M_NAME, M_SURNAME, M_AUTH0_ID, M_ROLE_ID,
                                M_TEAM_ID
                                )

from base_test import BaseTestCase
from misc import make_url, MatchParam, UserType, Expect
from test_data import (EqualDataMixin, ROLES, UserData, MANAGER_ROLE,
                       PLAYER_ROLE
                       )
from test_teams import TeamsTestCase, TEAMS_KEY_LIST, TEAM_1, TEAM_2

USERS = {
    # Keys are 'manager1' etc.
    f'{MANAGER_ROLE}{k}': UserData(0, f'manny{k}', f'm_surname{k}',
                                   f'auth0|m_id{k}', 0, 0)
    for k in TEAMS_KEY_LIST
}
USERS.update({
    # Keys are 'player1' etc.
    f'{PLAYER_ROLE}{k}': UserData(0, f'poly{k}', f'p_surname{k}',
                                  f'auth0|m_id{len(TEAMS_KEY_LIST) + int(k)}',
                                  0, 0)
    for k in TEAMS_KEY_LIST
})


class UserAttribMods(Enum):
    NAME = 0                # valid/invalid name
    SURNAME = 1             # valid/invalid surname
    AUTH0_ID_VALID = 2      # valid/invalid auth0_id
    AUTH0_ID_UNIQUE = 3     # unique/non-unique auth0_id
    ROLE_ID = 4             # valid/invalid role_id
    TEAM_ID = 5             # valid/invalid team_id


class UsersTestCase(BaseTestCase):
    """This class represents the test case for users."""

    users = {}
    teams = {}

    def setUp(self):
        """
        Method called to prepare the test fixture.
        This is called immediately before calling the test method.
        """
        super().setUp()

        # Add required users and teams.
        self.users, self.teams = UsersTestCase.setup_test_users_teams(self)

    @staticmethod
    def setup_test_users_teams(test_case: BaseTestCase) -> tuple[dict, dict]:
        """
        Setup users and teams for tests.
        :param test_case:   BaseTestCase instance
        :return
            users {     # key is '{user type}{user number}'
                'manager1': {<user dict>},
                'player1': {<user dict>},
                ...
            },
            teams {     # key is '{team number}'
                '1': {<team dict>},
                ...
            }
        """
        teams = TeamsTestCase.setup_test_teams(test_case)

        users = {}
        with test_case.app.app_context():
            # Add required users.
            for k, u in USERS.items():
                # Use role name at start of key to associate role
                # (i.e. MANAGER_ROLE/PLAYER_ROLE).
                u.role_id = ROLES[k[0:-1]].id
                # Use number id at end of key to associate team.
                u.team_id = teams[k[-1]][M_ID]
                user = u.to_model(ignore=[M_ID])
                test_case.db.session.add(user)
                test_case.db.session.flush()
                u.id = user.id

                users[k] = u.to_dict()

            test_case.db.session.commit()

        return users, teams

    def tearDown(self):
        """
        Method called immediately after the test method has been called
        and the result recorded.
        """
        super().tearDown()

    def assert_user(self, expected: Union[EqualDataMixin, dict], actual: dict,
                    msg: str = None):
        """
        Assert users are equal.
        """
        if msg is None:
            msg = ""
        if isinstance(expected, EqualDataMixin):
            self.assert_equal_data(expected, actual, ignore=None)
        else:
            self.assert_equal_dict(expected, actual, ignore=None)

    def assert_users_list(self, expected: list[EqualDataMixin], actual: list,
                          msg: str = None):
        """
        Assert users lists are equal.
        """
        if msg is None:
            msg = ""
        self.assertEqual(len(expected), len(actual),
                         f'Length mismatch for {msg}')
        index = 0
        for actual_user in actual:
            with self.subTest(actual_user=actual_user):
                self.assert_user(expected[index], actual_user,
                                 msg=f'user {index} {msg}')
                index = index + 1

    def assert_users_list_resp(self, expect: Expect, resp: Response,
                               expected: list[EqualDataMixin],
                               http_status: Union[
                                   HTTPStatus, range] = HTTPStatus.OK,
                               msg: str = None):
        """
        Assert users list responses are equal.
        :param expect:      Expected result; one of Expect.SUCCESS or
                            Expect.FAILURE
        :param resp:        response body
        :param expected:    expected list
        :param http_status: expected HTTPStatus or range of status codes
        :param msg:         assert error message
        """
        if msg is None:
            msg = ""

        self.assertTrue(resp.is_json)
        resp_body = resp.get_json()

        if expect == Expect.SUCCESS:
            self.assert_ok(resp.status_code)

            self.assert_success_response(resp_body)
            self.assert_body_entry(resp_body, RESULT_LIST_USERS,
                                   MatchParam.IGNORE)
            resp_users = resp_body[RESULT_LIST_USERS]

            self.assert_users_list(expected, resp_users, msg=msg)
        else:
            if isinstance(http_status, HTTPStatus):
                self.assert_response_status_code(http_status,
                                                 resp.status_code, msg=msg)

            self.assertTrue(resp.is_json)
            self.assert_error_response(resp_body, http_status, '',
                                       MatchParam.IGNORE, msg=msg)

    def assert_user_resp(self, expect: Expect, resp: Response,
                         expected: EqualDataMixin,
                         http_status: Union[
                             HTTPStatus, range] = HTTPStatus.OK,
                         msg: str = None):
        """
        Assert user response is equal.
        :param expect:      Expected result; one of Expect.SUCCESS or
                            Expect.FAILURE
        :param resp:        response body
        :param expected:    expected entity
        :param http_status: expected HTTPStatus or range of status codes
        :param msg:         assert error message
        """
        if msg is None:
            msg = ""

        self.assertTrue(resp.is_json)
        resp_body = resp.get_json()

        if expect == Expect.SUCCESS:
            self.assert_ok(resp.status_code)
            self.assert_success_response(resp_body)
            self.assert_body_entry(resp_body, RESULT_ONE_USER, MatchParam.EQUAL,
                                   value=expected)
        else:
            if isinstance(http_status, HTTPStatus):
                self.assert_response_status_code(http_status,
                                                 resp.status_code, msg=msg)

            self.assertTrue(resp.is_json)
            self.assert_error_response(resp_body, http_status, '',
                                       MatchParam.IGNORE, msg=msg)

    def test_get_all_users(self):
        """
        Test get all users.
        """
        with self.client as client:
            for user in UserType:
                permissions = self.set_permissions(user)

                with self.subTest(user=user):
                    resp = client.get(
                        make_url(USERS_URL)
                    )

                    has = BaseTestCase.has_permission(
                        permissions, GET_USER_PERMISSION)
                    expect = Expect.SUCCESS if has else Expect.FAILURE
                    if has:
                        http_status = HTTPStatus.OK
                    else:
                        http_status = HTTPStatus.UNAUTHORIZED

                    self.assert_users_list_resp(
                        expect, resp, [v for v in self.users.values()],
                        http_status=http_status)

    def test_get_user_by_id(self):
        """
        Test get users by id.
        """
        with self.client as client:
            for user in UserType:
                permissions = self.set_permissions(user)

                with self.subTest(user=user):
                    for v in self.users.values():
                        with self.subTest(value=v):
                            uid = v.id \
                                if isinstance(v, EqualDataMixin) else v[M_ID]
                            resp = client.get(
                                make_url(USER_BY_ID_URL, user_id=uid)
                            )

                            has = BaseTestCase.has_permission(
                                permissions, GET_USER_PERMISSION)
                            expect = Expect.SUCCESS if has else Expect.FAILURE
                            if has:
                                http_status = HTTPStatus.OK
                            else:
                                http_status = HTTPStatus.UNAUTHORIZED

                            expected = v.to_dict() \
                                if isinstance(v, EqualDataMixin) else v
                            self.assert_user_resp(
                                expect, resp, expected,
                                http_status=http_status)

    def test_get_user_by_invalid_id(self):
        """
        Test get user by an invalid id.
        """
        with self.client as client:
            for user in UserType:
                permissions = self.set_permissions(user)

                with self.subTest(user=user):
                    resp = client.get(
                        make_url(USER_BY_ID_URL, user_id=1000)
                    )

                    has = BaseTestCase.has_permission(
                        permissions, GET_USER_PERMISSION)
                    expect = Expect.SUCCESS if has else Expect.FAILURE
                    if has:
                        http_status = HTTPStatus.NOT_FOUND
                    else:
                        http_status = HTTPStatus.UNAUTHORIZED

                    self.assert_response_status_code(http_status,
                                                     resp.status_code)

                    self.assertTrue(resp.is_json)
                    self.assert_error_response(resp.get_json(),
                                               http_status.value,
                                               http_status.phrase,
                                               MatchParam.CASE_INSENSITIVE,
                                               MatchParam.IN)

    def _create_user(self, expect: Expect, new_user: Union[UserData, dict],
                     http_status: Union[HTTPStatus, range] = HTTPStatus.OK,
                     tag: str = None):
        """
        Create a user
        :param expect:   Expected result; one of Expect.SUCCESS or
                         Expect.FAILURE
        :param new_user: user to create
        """
        result = None
        if isinstance(new_user, UserData):
            new_user_dict = new_user.to_dict(ignore=[M_ID])
        else:
            new_user_dict = new_user
        msg = f'{new_user} {tag if tag is not None else ""}'
        with self.client as client:
            resp = client.post(USERS_URL, json=new_user_dict)

            resp_body = json.loads(resp.data)
            if expect == Expect.SUCCESS:
                self.assert_created(resp.status_code, msg=msg)
                self.assert_success_response(resp_body, msg=msg)
                self.assert_body_entry(resp_body, RESULT_CREATED_COUNT,
                                       MatchParam.EQUAL, value=1, msg=msg)
                self.assertTrue(RESULT_ONE_USER in resp_body.keys(), msg=msg)
                self.assert_equal_dict(
                    new_user_dict, resp_body[RESULT_ONE_USER], ignore=[M_ID])
                result = resp_body[RESULT_ONE_USER]
            else:
                if isinstance(http_status, HTTPStatus):
                    self.assert_response_status_code(http_status,
                                                     resp.status_code, msg=msg)

                self.assertTrue(resp.is_json)
                self.assert_error_response(resp_body, http_status, '',
                                           MatchParam.IGNORE, msg=msg)
        return result

    def test_create_user(self):
        """ Test create a user """
        for user in UserType:
            with self.subTest(user=user):
                permissions = self.set_permissions(user)

                # auth0_id has unique constraint.
                unique_auth0_id = "auth0_id_test_create_user"
                new_user = UserData(
                    0, name=f"{user} name", surname=f"{user} surname",
                    auth0_id=f"{user} {unique_auth0_id}",
                    role_id=ROLES[MANAGER_ROLE].id,
                    team_id=self.teams[TEAM_1][M_ID]
                )

                has = BaseTestCase.has_permission(
                    permissions, POST_USER_PERMISSION)
                expect = Expect.SUCCESS if has else Expect.FAILURE
                if has:
                    http_status = HTTPStatus.OK
                else:
                    http_status = HTTPStatus.UNAUTHORIZED

                self._create_user(expect, new_user, http_status=http_status)

    def modified_copy(self, user: dict, index: UserAttribMods, valid: bool,
                      unique_auth0_id: str = '',
                      non_unique_auth0_id: str = '',
                      role_id: int = 0, team_id: int = 0) -> tuple[dict, str]:
        """
        Create a modified copy of the specified user.
        :param user:                user to copy
        :param index:               index of attribute to modify
        :param valid:               attribute validity flag
        :param unique_auth0_id:     valid unique auth0_id
        :param non_unique_auth0_id: invalid auth0_id
        :param role_id:             valid role id
        :param team_id:             valid team id
        :return:
        """
        mod_user = deepcopy(user)
        if index == UserAttribMods.NAME:
            if valid:
                mod_user[M_NAME] = f"{mod_user[M_NAME]}_mod"
                info = "modified name"
            else:
                mod_user[M_NAME] = "   "
                info = "empty name"
        elif index == UserAttribMods.SURNAME:
            if valid:
                mod_user[M_SURNAME] = f"{mod_user[M_SURNAME]}_mod"
                info = "modified surname"
            else:
                mod_user[M_SURNAME] = "   "
                info = "empty surname"
        elif index == UserAttribMods.AUTH0_ID_VALID:
            if valid:
                mod_user[M_AUTH0_ID] = f"{unique_auth0_id}"
                info = "valid auth0_id"
            else:
                mod_user[M_AUTH0_ID] = "   "
                info = "empty auth0_id"
        elif index == UserAttribMods.AUTH0_ID_UNIQUE:
            if valid:
                mod_user[M_AUTH0_ID] = f"{unique_auth0_id}"
                info = "unique auth0_id"
            else:
                mod_user[M_AUTH0_ID] = f"{non_unique_auth0_id}"
                info = "non-unique auth0_id"
        elif index == UserAttribMods.ROLE_ID:
            if valid:
                mod_user[M_ROLE_ID] = role_id
                info = "valid role"
            else:
                mod_user[M_ROLE_ID] = 0
                info = "invalid role"
        elif index == UserAttribMods.TEAM_ID:
            if valid:
                mod_user[M_TEAM_ID] = team_id
                info = "valid team"
            else:
                mod_user[M_TEAM_ID] = 0
                info = "invalid team"
        else:
            self.fail(f"Unexpected index {index}")

        return mod_user, info

    def test_create_invalid_user(self):
        """ Test creating an invalid user """
        self.set_permissions(UserType.MANAGER)

        # auth0_id has unique constraint.
        unique_auth0_id = "auth0_id_test_create_invalid_user"
        ok_user = UserData(
            0, name="name", surname="surname", auth0_id=unique_auth0_id,
            role_id=ROLES['manager'].id, team_id=self.teams[TEAM_1][M_ID]
        )
        ok_user = self._create_user(Expect.SUCCESS, ok_user)

        for index in UserAttribMods:
            with self.subTest(index=index):
                bad_user, info = self.modified_copy(
                    ok_user, index, False,
                    unique_auth0_id=f'{unique_auth0_id}_unique',
                    non_unique_auth0_id=unique_auth0_id,
                    role_id=ROLES[MANAGER_ROLE].id,
                    team_id=self.teams[TEAM_1][M_ID]
                )

                self._create_user(Expect.FAILURE, bad_user,
                                  http_status=range(400, 500),
                                  tag=f'index {index} {info}')

    def _delete_user(self, expect: Expect, user_id: int,
                     http_status: Union[HTTPStatus, range] = HTTPStatus.OK):
        """
        Create a user
        :param expect:   Expected result; one of Expect.SUCCESS or
                         Expect.FAILURE
        """
        msg = f'user_id {user_id}'
        with self.client as client:
            resp = client.delete(
                make_url(USER_BY_ID_URL, user_id=user_id)
            )

            resp_body = json.loads(resp.data)
            if expect == Expect.SUCCESS:
                self.assert_ok(resp.status_code, msg=msg)
                self.assert_success_response(resp_body, msg=msg)
                self.assert_body_entry(resp_body, RESULT_DELETED_COUNT,
                                       MatchParam.EQUAL, value=1, msg=msg)
            else:
                if isinstance(http_status, HTTPStatus):
                    self.assert_response_status_code(http_status,
                                                     resp.status_code, msg=msg)

                self.assertTrue(resp.is_json)
                self.assert_error_response(resp_body, http_status, '',
                                           MatchParam.IGNORE, msg=msg)

    def test_delete_user(self):
        """ Test deleting a user """
        for user in UserType:
            with self.subTest(user=user):
                permissions = self.set_permissions(user)

                has = BaseTestCase.has_permission(
                    permissions, POST_USER_PERMISSION)
                if has:
                    # auth0_id has unique constraint.
                    unique_auth0_id = f"auth0_id_test_delete_user {user}"
                    new_user = UserData(
                        0, name=f"{user}", surname="Short-Lived",
                        auth0_id=unique_auth0_id,
                        role_id=ROLES[MANAGER_ROLE].id,
                        team_id=self.teams[TEAM_1][M_ID]
                    )
                    # Create user to delete
                    to_delete = self._create_user(Expect.SUCCESS, new_user)
                    delete_id = to_delete[M_ID]
                else:
                    delete_id = 1   # Arbitrary id, should not have access.

                has = BaseTestCase.has_permission(
                    permissions, DELETE_USER_PERMISSION)
                if not has:
                    has = BaseTestCase.has_permission(
                        permissions, DELETE_OWN_USER_PERMISSION)
                expect = Expect.SUCCESS if has else Expect.FAILURE
                if has:
                    http_status = HTTPStatus.OK
                else:
                    http_status = HTTPStatus.UNAUTHORIZED

                self._delete_user(expect, delete_id, http_status=http_status)

    def test_delete_invalid_user(self):
        """ Test deleting an invalid user """
        self.set_permissions(UserType.MANAGER)

        self._delete_user(Expect.FAILURE, 1000,
                          http_status=HTTPStatus.NOT_FOUND)

    def _update_user(self, expect: Expect, user_id: int, old_user: dict,
                     new_user: dict, tag: str,
                     http_status: Union[HTTPStatus, range] = HTTPStatus.OK):
        """
        Create a user
        :param expect:   Expected result; one of Expect.SUCCESS or
                         Expect.FAILURE
        """
        updates = {}
        for k, v in old_user.items():
            new_v = new_user[k]
            if new_v != v:
                updates[k] = new_v

        msg = f'user_id {user_id} {old_user} -> {new_user} = {updates} ' \
              f'{tag if tag is not None else ""}'
        with self.client as client:
            resp = client.patch(
                make_url(USER_BY_ID_URL, user_id=user_id), json=updates
            )

            resp_body = json.loads(resp.data)
            if expect == Expect.SUCCESS:
                self.assert_ok(resp.status_code, msg=msg)
                self.assert_success_response(resp_body, msg=msg)
                self.assert_body_entry(resp_body, RESULT_UPDATED_COUNT,
                                       MatchParam.EQUAL, value=1, msg=msg)
                self.assert_body_entry(resp_body, RESULT_ONE_USER,
                                       MatchParam.EQUAL, value=new_user,
                                       msg=msg)
            else:
                if isinstance(http_status, HTTPStatus):
                    self.assert_response_status_code(http_status,
                                                     resp.status_code, msg=msg)

                self.assertTrue(resp.is_json)
                self.assert_error_response(resp_body, http_status, '',
                                           MatchParam.IGNORE, msg=msg)

    def test_update_user(self):
        """ Test updating a user """
        self.set_permissions(UserType.MANAGER)

        # Create user which will not change.
        no_change_user = UserData(
            0, name=f"No", surname="Change",
            auth0_id=f"auth0_id_test_update_user no change",
            role_id=ROLES[MANAGER_ROLE].id,
            team_id=self.teams[TEAM_1][M_ID]
        )
        no_change_user = self._create_user(Expect.SUCCESS, no_change_user)

        for user in UserType:
            with self.subTest(user=user):
                permissions = self.set_permissions(user)

                # auth0_id has unique constraint.
                unique_auth0_id = f"auth0_id_test_update_user {user}"

                has = BaseTestCase.has_permission(
                    permissions, POST_USER_PERMISSION)
                if has:
                    old_user = UserData(
                        0, name=f"{user}", surname="Swift-Change",
                        auth0_id=unique_auth0_id,
                        role_id=ROLES[MANAGER_ROLE].id,
                        team_id=self.teams[TEAM_1][M_ID]
                    )
                    # Create user to update
                    old_user = self._create_user(Expect.SUCCESS, old_user)
                else:
                    old_user = no_change_user

                has = BaseTestCase.has_permission(
                    permissions, PATCH_USER_PERMISSION)
                if not has:
                    has = BaseTestCase.has_permission(
                        permissions, PATCH_OWN_USER_PERMISSION)
                expect = Expect.SUCCESS if has else Expect.FAILURE
                if has:
                    if old_user is None:
                        self.fail("No user to update")
                    http_status = HTTPStatus.OK
                else:
                    http_status = HTTPStatus.UNAUTHORIZED

                count = 0
                for index in UserAttribMods:
                    if count > 0 and http_status != HTTPStatus.OK:
                        # Does not have permission, so only need to test once.
                        continue
                    count = count + 1

                    if index == UserAttribMods.AUTH0_ID_UNIQUE:
                        # Skip modifying unique auth0_id
                        continue

                    with self.subTest(index=index):
                        mod_user, info = self.modified_copy(
                            old_user, index, True,
                            unique_auth0_id=f'{unique_auth0_id}_unique',
                            non_unique_auth0_id=unique_auth0_id,
                            role_id=ROLES[PLAYER_ROLE].id,
                            team_id=self.teams[TEAM_2][M_ID]
                        )

                        self._update_user(expect, old_user[M_ID],
                                          old_user, mod_user, info,
                                          http_status=http_status)
                        old_user = mod_user

    def test_update_user_invalid(self):
        """ Test updating a user """
        permissions = self.set_permissions(UserType.MANAGER)

        # auth0_id has unique constraint.
        unique_auth0_id = f"auth0_id_test_update_user_invalid"

        has = BaseTestCase.has_permission(
            permissions, POST_USER_PERMISSION)
        if has:
            old_user = UserData(
                0, name=f"Will", surname="Not-Change",
                auth0_id=unique_auth0_id,
                role_id=ROLES[MANAGER_ROLE].id,
                team_id=self.teams[TEAM_1][M_ID]
            )
            # Create user to update
            old_user = self._create_user(Expect.SUCCESS, old_user)
        else:
            self.fail("Could not create user")

        has = BaseTestCase.has_permission(
            permissions, PATCH_USER_PERMISSION)
        if not has:
            has = BaseTestCase.has_permission(
                permissions, PATCH_OWN_USER_PERMISSION)
        if has:
            if old_user is None:
                self.fail("No user to update")
            http_status = range(400, 500)
        else:
            self.fail("No user update permission")

        count = 0
        for index in UserAttribMods:
            if count > 0 and http_status != HTTPStatus.OK:
                # Does not have permission, so only need to test once.
                continue
            count = count + 1

            if index == UserAttribMods.AUTH0_ID_UNIQUE:
                # Skip modifying unique auth0_id
                continue

            with self.subTest(index=index):
                mod_user, info = self.modified_copy(
                    old_user, index, False,
                    unique_auth0_id=f'{unique_auth0_id}_unique',
                    non_unique_auth0_id=unique_auth0_id,
                    role_id=ROLES[PLAYER_ROLE].id,
                    team_id=self.teams[TEAM_2][M_ID]
                )

                self._update_user(Expect.FAILURE, old_user[M_ID],
                                  old_user, mod_user, info,
                                  http_status=http_status)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
