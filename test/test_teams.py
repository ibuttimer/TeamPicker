import json
import unittest
from copy import deepcopy
from http import HTTPStatus
from typing import Union

from flask import Response

from team_picker.constants import (TEAMS_URL, TEAM_BY_ID_URL,
                                   RESULT_ONE_ROLE, RESULT_LIST_TEAMS,
                                   RESULT_CREATED_COUNT, RESULT_ONE_TEAM,
                                   RESULT_DELETED_COUNT, RESULT_UPDATED_COUNT,
                                   POST_TEAM_PERMISSION, GET_TEAM_PERMISSION,
                                   )
from team_picker.models import M_ID, M_NAME, Team

from base_test import BaseTestCase
from misc import make_url, MatchParam, UserType, Expect
from test_data import EqualDataMixin, TeamData, UNASSIGNED_TEAM

TEAM_1 = '1'
TEAM_2 = '2'
TEAM_3 = '3'
TEAM_4 = '4'
TEAM_5 = '5'
TEAMS_KEY_LIST = [TEAM_1, TEAM_2, TEAM_3, TEAM_4, TEAM_5]
TEAMS = {
    k: TeamData(0, f"Team {k}")
    for k in TEAMS_KEY_LIST
}


class TeamsTestCase(BaseTestCase):
    """This class represents the test case for teams."""

    teams = {}

    def setUp(self):
        """
        Method called to prepare the test fixture.
        This is called immediately before calling the test method.
        """
        super().setUp()

        self.teams = TeamsTestCase.setup_test_teams(self)

    @staticmethod
    def setup_test_teams(test_case: BaseTestCase) -> dict:
        """
        Setup teams for tests.
        :param test_case:   BaseTestCase instance
        :return
            teams {     # key is '{team number}'
                '1': {<team dict>},
                ...
            }
        """
        teams = {
            UNASSIGNED_TEAM.name:
                TeamData(UNASSIGNED_TEAM.id, UNASSIGNED_TEAM.name).to_dict()
        }
        with test_case.app.app_context():
            # Add required teams.
            app_db = test_case.get_db()
            for k, team_data in TEAMS.items():
                team = team_data.to_model(ignore=[M_ID])
                app_db.session.add(team)
                app_db.session.flush()
                team_data.id = team.id

                teams[k] = team_data.to_dict()

            app_db.session.commit()

        return teams

    def tearDown(self):
        """
        Method called immediately after the test method has been called
        and the result recorded.
        """
        super().tearDown()

    def assert_team(self, expected: Union[EqualDataMixin, dict], actual: dict,
                    msg: str = None):
        """
        Assert teams are equal.
        """
        if msg is None:
            msg = ""
        if isinstance(expected, EqualDataMixin):
            self.assert_equal_data(expected, actual, ignore=None)
        else:
            self.assert_equal_dict(expected, actual, ignore=None)

    def assert_teams_list(self, expected: list[EqualDataMixin], actual: list,
                          msg: str = None):
        """
        Assert teams lists are equal.
        """
        if msg is None:
            msg = ""
        self.assertEqual(len(expected), len(actual),
                         f'Length mismatch for {msg}')
        index = 0
        for actual_team in actual:
            with self.subTest(actual_team=actual_team):
                self.assert_team(expected[index], actual_team,
                                 msg=f'team {index} {msg}')
                index = index + 1

    def assert_teams_list_resp(self, expect: Expect, resp: Response,
                               expected: list[EqualDataMixin],
                               http_status: Union[
                                   HTTPStatus, range] = HTTPStatus.OK,
                               msg: str = None):
        """
        Assert teams list responses are equal.
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
            self.assert_body_entry(resp_body, RESULT_LIST_TEAMS,
                                   MatchParam.IGNORE)
            resp_teams = resp_body[RESULT_LIST_TEAMS]

            self.assert_teams_list(expected, resp_teams, msg=msg)
        else:
            if isinstance(http_status, HTTPStatus):
                self.assert_response_status_code(http_status,
                                                 resp.status_code, msg=msg)

            self.assertTrue(resp.is_json)
            self.assert_error_response(resp_body, http_status, '',
                                       MatchParam.IGNORE, msg=msg)

    def assert_team_resp(self, expect: Expect, resp: Response,
                         expected: EqualDataMixin,
                         http_status: Union[
                             HTTPStatus, range] = HTTPStatus.OK,
                         msg: str = None):
        """
        Assert team response is equal.
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
            self.assert_body_entry(resp_body, RESULT_ONE_TEAM, MatchParam.EQUAL,
                                   value=expected)
        else:
            if isinstance(http_status, HTTPStatus):
                self.assert_response_status_code(http_status,
                                                 resp.status_code, msg=msg)

            self.assertTrue(resp.is_json)
            self.assert_error_response(resp_body, http_status, '',
                                       MatchParam.IGNORE, msg=msg)

    def test_get_all_teams(self):
        """
        Test get all teams to ensure valid users can access and others cannot.
        """
        with self.client as client:
            for user in UserType:
                permissions = self.set_permissions(user)

                with self.subTest(user=user):
                    resp = client.get(
                        make_url(TEAMS_URL)
                    )

                    has = BaseTestCase.has_permission(
                        permissions, GET_TEAM_PERMISSION)
                    expect = Expect.SUCCESS if has else Expect.FAILURE
                    if has:
                        http_status = HTTPStatus.OK
                    else:
                        http_status = HTTPStatus.UNAUTHORIZED

                    self.assert_teams_list_resp(
                        expect, resp, [v for v in self.teams.values()],
                        http_status=http_status, msg=f"{user}")

    def test_get_team_by_id(self):
        """
        Test get teams by id.
        """
        with self.client as client:
            for user in UserType:
                permissions = self.set_permissions(user)

                with self.subTest(user=user):
                    for k, v in self.teams.items():
                        with self.subTest(team=v):
                            resp = client.get(
                                make_url(TEAM_BY_ID_URL, team_id=v[M_ID])
                            )

                            has = BaseTestCase.has_permission(
                                permissions, GET_TEAM_PERMISSION)
                            expect = Expect.SUCCESS if has else Expect.FAILURE
                            if has:
                                http_status = HTTPStatus.OK
                            else:
                                http_status = HTTPStatus.UNAUTHORIZED

                            expected = v.to_dict() \
                                if isinstance(v, EqualDataMixin) else v
                            self.assert_team_resp(
                                expect, resp, expected,
                                http_status=http_status)

    def test_get_team_by_invalid_id(self):
        """
        Test get team by an invalid id.
        """
        with self.client as client:
            for user in UserType:
                permissions = self.set_permissions(user)

                with self.subTest(user=user):
                    resp = client.get(
                        make_url(TEAM_BY_ID_URL, team_id=1000)
                    )

                    has = BaseTestCase.has_permission(
                        permissions, GET_TEAM_PERMISSION)
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

    def _create_team(self, expect: Expect, new_team: TeamData,
                     http_status: Union[HTTPStatus, range] = HTTPStatus.OK,
                     tag: str = None):
        """
        Create a team
        :param expect:   Expected result; one of Expect.SUCCESS or
                         Expect.FAILURE
        :param new_team: team to create
        """
        result = None
        new_team_dict = new_team.to_dict(ignore=[M_ID])
        msg = f'{new_team} {tag if tag is not None else ""}'
        with self.client as client:
            resp = client.post(TEAMS_URL, json=new_team_dict)

            resp_body = json.loads(resp.data)
            if expect == Expect.SUCCESS:
                self.assert_created(resp.status_code, msg=msg)
                self.assert_success_response(resp_body, msg=msg)
                self.assert_body_entry(resp_body, RESULT_CREATED_COUNT,
                                       MatchParam.EQUAL, value=1, msg=msg)
                self.assertTrue(RESULT_ONE_TEAM in resp_body.keys(), msg=msg)
                self.assert_equal_dict(
                    new_team_dict, resp_body[RESULT_ONE_TEAM], ignore=[M_ID])
                result = resp_body[RESULT_ONE_TEAM]
            else:
                if isinstance(http_status, HTTPStatus):
                    self.assert_response_status_code(http_status,
                                                     resp.status_code, msg=msg)

                self.assertTrue(resp.is_json)
                self.assert_error_response(resp_body, http_status, '',
                                           MatchParam.IGNORE, msg=msg)
        return result

    def test_create_team(self):
        """ Test create a team """
        for user in UserType:
            with self.subTest(user=user):
                permissions = self.set_permissions(user)

                new_team = TeamData(0, f"Bueno {user} FC")

                has = BaseTestCase.has_permission(
                    permissions, POST_TEAM_PERMISSION)
                expect = Expect.SUCCESS if has else Expect.FAILURE
                if has:
                    http_status = HTTPStatus.OK
                else:
                    http_status = HTTPStatus.UNAUTHORIZED

                self._create_team(expect, new_team, http_status=http_status)

    def test_create_invalid_team(self):
        """ Test creating an invalid team """
        # Only managers can create teams.
        self.set_permissions(UserType.MANAGER)

        bad_team = TeamData(0, "")

        for index in range(1):
            with self.subTest(index=index):
                if index == 0:
                    bad_team.name = "   "
                    info = "empty name"
                else:
                    self.fail(f"Unexpected index {index}")

                self._create_team(Expect.FAILURE, bad_team,
                                  http_status=range(400, 500),
                                  tag=f'index {index} {info}')

    def test_create_duplicate_team(self):
        """ Test creating a duplicate team """
        # Only managers can create teams.
        self.set_permissions(UserType.MANAGER)

        new_team = TeamData(0, "The one and only")
        self._create_team(Expect.SUCCESS, new_team, http_status=HTTPStatus.OK)
        self._create_team(Expect.FAILURE, new_team, http_status=range(400, 500))

    def _delete_team(self, expect: Expect, team_id: int,
                     http_status: Union[HTTPStatus, range] = HTTPStatus.OK):
        """
        Create a team
        :param expect:   Expected result; one of Expect.SUCCESS or
                         Expect.FAILURE
        """
        msg = f'team_id {team_id}'
        with self.client as client:
            resp = client.delete(
                make_url(TEAM_BY_ID_URL, team_id=team_id)
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

    def test_delete_team(self):
        """ Test deleting a team """
        # Only managers can create teams.
        self.set_permissions(UserType.MANAGER)

        new_team = TeamData(0, "Short lived")
        created_team = self._create_team(Expect.SUCCESS, new_team,
                                         http_status=HTTPStatus.OK)

        for user in UserType:
            with self.subTest(user=user):
                permissions = self.set_permissions(user)

                has = BaseTestCase.has_permission(
                    permissions, POST_TEAM_PERMISSION)
                expect = Expect.SUCCESS if has else Expect.FAILURE
                if has:
                    http_status = HTTPStatus.OK
                else:
                    http_status = HTTPStatus.UNAUTHORIZED

                self._delete_team(expect, created_team[M_ID],
                                  http_status=http_status)

    def test_delete_invalid_team(self):
        """ Test deleting an invalid team """
        # Only managers can delete teams.
        self.set_permissions(UserType.MANAGER)

        self._delete_team(Expect.FAILURE, 1000,
                          http_status=HTTPStatus.NOT_FOUND)

    def _update_team(self, expect: Expect, team_id: int, old_team: dict,
                     new_team: dict, tag: str,
                     http_status: Union[HTTPStatus, range] = HTTPStatus.OK):
        """
        Create a team
        :param expect:   Expected result; one of Expect.SUCCESS or
                         Expect.FAILURE
        """
        updates = {}
        for k, v in old_team.items():
            new_v = new_team[k]
            if new_v != v:
                updates[k] = new_v

        msg = f'team_id {team_id} {old_team} -> {new_team} = {updates} ' \
              f'{tag if tag is not None else ""}'
        with self.client as client:
            resp = client.patch(
                make_url(TEAM_BY_ID_URL, team_id=team_id), json=updates
            )

            resp_body = json.loads(resp.data)
            if expect == Expect.SUCCESS:
                self.assert_ok(resp.status_code, msg=msg)
                self.assert_success_response(resp_body, msg=msg)
                self.assert_body_entry(resp_body, RESULT_UPDATED_COUNT,
                                       MatchParam.EQUAL, value=1, msg=msg)
                self.assert_body_entry(resp_body, RESULT_ONE_TEAM,
                                       MatchParam.EQUAL, value=new_team,
                                       msg=msg)
            else:
                if isinstance(http_status, HTTPStatus):
                    self.assert_response_status_code(http_status,
                                                     resp.status_code, msg=msg)

                self.assertTrue(resp.is_json)
                self.assert_error_response(resp_body, http_status, '',
                                           MatchParam.IGNORE, msg=msg)

    def test_update_team(self):
        """ Test updating a team """
        # Only managers can create teams.
        self.set_permissions(UserType.MANAGER)

        new_team = TeamData(0, "Change can be swift")
        created_team = self._create_team(Expect.SUCCESS, new_team,
                                         http_status=HTTPStatus.OK)

        for index in range(1):
            with self.subTest(index=index):
                if index == 0:
                    # Change name
                    old_team = created_team
                    new_team = deepcopy(old_team)
                    new_team[M_NAME] = f"{new_team[M_NAME]} and sudden"
                    tag = "name"
                else:
                    self.fail(f"Unexpected index {index}")

                for user in UserType:
                    if index > 0 and user != UserType.MANAGER:
                        # Only manager's can update, so only need to test
                        # others once.
                        continue

                    with self.subTest(user=user):
                        permissions = self.set_permissions(user)

                        has = BaseTestCase.has_permission(
                            permissions, POST_TEAM_PERMISSION)
                        expect = Expect.SUCCESS if has else Expect.FAILURE
                        if has:
                            http_status = HTTPStatus.OK
                        else:
                            http_status = HTTPStatus.UNAUTHORIZED

                        self._update_team(expect, created_team[M_ID],
                                          old_team, new_team, tag,
                                          http_status=http_status)

    def test_update_team_invalid(self):
        """ Test updating a team """
        # Only managers can create and update teams.
        self.set_permissions(UserType.MANAGER)

        new_team = TeamData(0, "Change can be hard")
        created_team = self._create_team(Expect.SUCCESS, new_team,
                                         http_status=HTTPStatus.OK)

        for index in range(1):
            with self.subTest(index=index):
                if index == 0:
                    # Empty name
                    old_team = created_team
                    new_team = deepcopy(old_team)
                    new_team[M_NAME] = "  "
                    tag = "empty name"
                else:
                    self.fail(f"Unexpected index {index}")

                self._update_team(Expect.FAILURE, created_team[M_ID],
                                  old_team, new_team, tag,
                                  http_status=range(400, 500))


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
