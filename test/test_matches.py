import json
import unittest
from copy import deepcopy
from datetime import datetime, timedelta
from enum import IntEnum, auto
from http import HTTPStatus
from typing import Union, Optional

from flask import Response

from team_picker.constants import (MATCHES_URL, MATCH_BY_ID_URL,
                                   RESULT_ONE_MATCH, RESULT_LIST_MATCHES,
                                   RESULT_CREATED_COUNT,
                                   RESULT_DELETED_COUNT, RESULT_UPDATED_COUNT,
                                   POST_MATCH_PERMISSION, GET_MATCH_PERMISSION,
                                   DELETE_MATCH_PERMISSION,
                                   PATCH_MATCH_PERMISSION,
                                   )
from team_picker.models import (M_ID, M_START_TIME, M_SELECTIONS, User,
                                M_HOME_ID, M_AWAY_ID, M_SCORE_HOME,
                                M_SCORE_AWAY, M_RESULT
                                )

from base_test import BaseTestCase
from misc import make_url, MatchParam, UserType, Expect
from test_data import EqualDataMixin, ROLES, UserData, MatchData, PLAYER_ROLE
from test_teams import TEAM_1, TEAM_2, TEAM_3, TEAM_4, TEAM_5
from test_users import UsersTestCase


class MatchAttribMods(IntEnum):
    HOME_TEAM = auto()  # valid/invalid home team id
    AWAY_TEAM = auto()  # valid/invalid away team id
    SCORE_HOME = auto()  # valid/invalid home score
    SCORE_AWAY = auto()  # valid/invalid away score
    START_TIME = auto()  # valid/invalid start_time conflict
    SELECTIONS = auto()  # valid/invalid selections

    DUPLICATE_TEAM_CONFLICT = auto()  # valid/invalid same team as home & away
    DUPLICATE_MATCH_CONFLICT = auto()  # valid/invalid same teams & time
    HOME_CONFLICT = auto()  # valid/invalid home team & time conflict
    AWAY_CONFLICT = auto()  # valid/invalid away team & time conflict
    # valid/invalid home team home & away fixture time conflict
    HOME_AWAY_CONFLICT = auto()
    # valid/invalid away team home & away fixture time conflict
    AWAY_HOME_CONFLICT = auto()


# Modification that have valid change values.
HAVE_VALID_CHANGES = [MatchAttribMods.HOME_TEAM,
                      MatchAttribMods.AWAY_TEAM,
                      MatchAttribMods.SCORE_HOME,
                      MatchAttribMods.SCORE_AWAY,
                      MatchAttribMods.START_TIME,
                      MatchAttribMods.SELECTIONS
                      ]

MATCH_KEY = 'home-away'


class MatchesTestCase(BaseTestCase):
    """This class represents the test case for matches."""

    users = {}
    teams = {}
    matches = {}

    def setUp(self):
        """
        Method called to prepare the test fixture.
        This is called immediately before calling the test method.
        """
        super().setUp()

        # Add required users and teams.
        self.users, self.teams, self.matches = \
            MatchesTestCase.setup_test_users_teams_matches(self)

    @staticmethod
    def setup_test_users_teams_matches(
            test_case: BaseTestCase) -> tuple[dict, dict, dict]:
        """
        Setup users, teams and matches for tests.
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
            },
            matches {   # key is '{home team number}home-away{away team number}'
                '1home-away2': {<team dict>},
                ...
            }
        """
        # Add required users and teams.
        users, teams = UsersTestCase.setup_test_users_teams(test_case)

        matches = {}
        with test_case.app.app_context():
            # Get player models
            players = {}
            for k, u in users.items():
                if k.startswith(PLAYER_ROLE):
                    players[k] = test_case.db.session.query(User) \
                        .filter(User.id == u[M_ID]) \
                        .first()

            # Add required matches.
            for k, m in {
                f'1{MATCH_KEY}2':
                    MatchData(0, 0, 0, datetime(2021, 6, 19, 12, 30),
                              True, 1, 2, []),
                f'2{MATCH_KEY}1':
                    MatchData(0, 0, 0, datetime(2021, 6, 26, 14, 0),
                              False, 2, 1, []),
            }.items():
                # Use team number at start of key to associate home team.
                home_num = k[:1]
                m.home_id = teams[home_num][M_ID]
                # Use team number at end of key to associate away team.
                away_num = k[-1]
                m.away_id = teams[away_num][M_ID]
                match = m.to_model(ignore=[M_ID, M_SELECTIONS])

                test_case.db.session.add(match)
                test_case.db.session.flush()
                m.id = match.id

                # Use team numbers to add player selections
                for num in [home_num, away_num]:
                    key = f"{PLAYER_ROLE}{num}"
                    m.selections.append(users[key])
                    match.selections.append(players[key])

                test_case.db.session.flush()

                matches[k] = m.to_dict()
                # Standardise selection to ascending player id order.
                matches[k][M_SELECTIONS].sort(key=lambda s: s[M_ID])

            test_case.db.session.commit()

        return users, teams, matches

    def tearDown(self):
        """
        Method called immediately after the test method has been called
        and the result recorded.
        """
        super().tearDown()

    def assert_match(self, expected: Union[EqualDataMixin, dict], actual: dict,
                     msg: str = None):
        """
        Assert matches are equal.
        """
        if msg is None:
            msg = ""
        if isinstance(expected, EqualDataMixin):
            self.assert_equal_data(expected, actual, ignore=None)
        else:
            self.assert_equal_dict(expected, actual, ignore=None)

    def assert_matches_list(self, expected: list[EqualDataMixin], actual: list,
                            msg: str = None):
        """
        Assert matches lists are equal.
        """
        if msg is None:
            msg = ""
        self.assertEqual(len(expected), len(actual),
                         f'Length mismatch for {msg}')
        index = 0
        for actual_match in actual:
            with self.subTest(actual_match=actual_match):
                self.assert_match(expected[index], actual_match,
                                  msg=f'match {index} {msg}')
                index = index + 1

    def assert_matches_list_resp(self, expect: Expect, resp: Response,
                                 expected: list[EqualDataMixin],
                                 http_status: Union[
                                     HTTPStatus, range] = HTTPStatus.OK,
                                 msg: str = None):
        """
        Assert matches list responses are equal.
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
            self.assert_body_entry(resp_body, RESULT_LIST_MATCHES,
                                   MatchParam.IGNORE)
            resp_matches = resp_body[RESULT_LIST_MATCHES]

            self.assert_matches_list(expected, resp_matches, msg=msg)
        else:
            if isinstance(http_status, HTTPStatus):
                self.assert_response_status_code(http_status,
                                                 resp.status_code, msg=msg)

            self.assertTrue(resp.is_json)
            self.assert_error_response(resp_body, http_status, '',
                                       MatchParam.IGNORE, msg=msg)

    def assert_match_resp(self, expect: Expect, resp: Response,
                          expected: EqualDataMixin,
                          http_status: Union[
                              HTTPStatus, range] = HTTPStatus.OK,
                          msg: str = None):
        """
        Assert matches list responses are equal.
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
            self.assert_body_entry(resp_body, RESULT_ONE_MATCH,
                                   MatchParam.EQUAL,
                                   value=expected)
        else:
            if isinstance(http_status, HTTPStatus):
                self.assert_response_status_code(http_status,
                                                 resp.status_code, msg=msg)

            self.assertTrue(resp.is_json)
            self.assert_error_response(resp_body, http_status, '',
                                       MatchParam.IGNORE, msg=msg)

    @staticmethod
    def standardise_match(
            match: Union[MatchData, dict]) -> Union[MatchData, dict]:
        # Transform start_time to iso format to match server response.
        std_match = deepcopy(match)
        if isinstance(match, MatchData):
            std_match.start_time = match.start_time.isoformat()
        else:  # dict
            if isinstance(std_match[M_START_TIME], datetime):
                std_match[M_START_TIME] = match[M_START_TIME].isoformat()
            # Else str already in iso format.
        return std_match

    def test_get_all_matches(self):
        """
        Test get all matches.
        """
        expected_list = [v for v in self.matches.values()]

        with self.client as client:
            for user in UserType:
                permissions = self.set_permissions(user)

                with self.subTest(user=user):
                    resp = client.get(
                        make_url(MATCHES_URL)
                    )

                    has = BaseTestCase.has_permission(
                        permissions, GET_MATCH_PERMISSION)
                    expect = Expect.SUCCESS if has else Expect.FAILURE
                    if has:
                        http_status = HTTPStatus.OK
                    else:
                        http_status = HTTPStatus.UNAUTHORIZED

                    self.assert_matches_list_resp(expect, resp, expected_list,
                                                  http_status=http_status)

    def test_get_match_by_id(self):
        """
        Test get matches by id.
        """
        with self.client as client:
            for user in UserType:
                permissions = self.set_permissions(user)

                with self.subTest(user=user):
                    for m in self.matches.values():
                        std_match = m
                        # std_match = MatchesTestCase.standardise_match(m)
                        with self.subTest(value=std_match):
                            uid = std_match.id \
                                if isinstance(std_match, EqualDataMixin) \
                                else std_match[M_ID]
                            resp = client.get(
                                make_url(MATCH_BY_ID_URL, match_id=uid)
                            )

                            has = BaseTestCase.has_permission(
                                permissions, GET_MATCH_PERMISSION)
                            expect = Expect.SUCCESS if has else Expect.FAILURE
                            if has:
                                http_status = HTTPStatus.OK
                            else:
                                http_status = HTTPStatus.UNAUTHORIZED

                            expected = std_match.to_dict() \
                                if isinstance(std_match, EqualDataMixin) \
                                else std_match

                            self.assert_match_resp(expect, resp, expected,
                                                   http_status=http_status)

    def test_get_match_by_invalid_id(self):
        """
        Test get match by an invalid id.
        """
        with self.client as client:
            for user in UserType:
                permissions = self.set_permissions(user)

                with self.subTest(user=user):
                    resp = client.get(
                        make_url(MATCH_BY_ID_URL, match_id=1000)
                    )

                    has = BaseTestCase.has_permission(
                        permissions, GET_MATCH_PERMISSION)
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

    @staticmethod
    def find_user(testcase: BaseTestCase, users: dict, uid: int):
        """
        Find the user with the specified id.
        :param testcase: test case
        :param users: dict of user dicts of the form {
                <user id>: {<user dict>},
                <user id>: {<user dict>},
                ...
            }
        :param uid: id of user to find
        :return:
        """
        for u in users.values():
            if u[M_ID] == uid:
                user = u
                break
        else:
            testcase.fail(f"User id {uid} not found")
        return user

    @staticmethod
    def create_match(testcase: BaseTestCase, expect: Expect,
                     new_match: Union[MatchData, dict],
                     users: dict = None,
                     http_status: Union[HTTPStatus, range] = HTTPStatus.OK,
                     tag: str = None) -> Optional[dict]:
        """
        Create a match
        :param testcase: test case
        :param expect:   Expected result; one of Expect.SUCCESS or
                         Expect.FAILURE
        :param new_match: match to create
        :param users: dict of user dicts of the form {
                <user id>: {<user dict>},
                <user id>: {<user dict>},
                ...
            }
        :param http_status: expected HTTPStatus or range of status codes
        :param tag: identifier tag
        :return dict of created match if applicable
        """
        if users is None:
            users = {}
        result = None
        if isinstance(new_match, MatchData):
            new_match_dict = new_match.to_dict(ignore=[M_ID])
        else:
            new_match_dict = new_match
        new_match_dict = MatchesTestCase.standardise_match(new_match_dict)

        # Create expected result match dict.
        expected = deepcopy(new_match_dict)
        if M_SELECTIONS in expected.keys():
            # Set selections to player dicts.
            if expect == Expect.SUCCESS:
                selections = expected[M_SELECTIONS]
                if len(selections) > 0 and isinstance(selections[0], int):
                    expected[M_SELECTIONS] = [
                        MatchesTestCase.find_user(testcase, users, uid)
                        for uid in selections
                    ]
                    # Order selections by user id.
                    expected[M_SELECTIONS].sort(key=lambda x: x[M_ID])

        msg = f'{new_match} {tag if tag is not None else ""}'
        with testcase.client as client:
            resp = client.post(MATCHES_URL, json=new_match_dict)

            resp_body = json.loads(resp.data)
            if expect == Expect.SUCCESS:
                testcase.assert_created(resp.status_code, msg=msg)
                testcase.assert_success_response(resp_body, msg=msg)
                testcase.assert_body_entry(resp_body, RESULT_CREATED_COUNT,
                                           MatchParam.EQUAL, value=1, msg=msg)
                testcase.assertTrue(
                    RESULT_ONE_MATCH in resp_body.keys(), msg=msg)
                testcase.assert_equal_dict(
                    expected, resp_body[RESULT_ONE_MATCH], ignore=[M_ID])
                result = resp_body[RESULT_ONE_MATCH]
            else:
                if isinstance(http_status, HTTPStatus):
                    testcase.assert_response_status_code(
                        http_status, resp.status_code, msg=msg)

                testcase.assertTrue(resp.is_json)
                testcase.assert_error_response(
                    resp_body, http_status, '', MatchParam.IGNORE, msg=msg)
        return result

    def user_ids_list(self, role: str, ids: list[str]):
        """
        Create a list of user ids.
        :param role: User role from key; i.e. '{role}{index}'
        :param ids:  User index
        :return:
        """
        return [
            self.users[f'{role}{p}'][M_ID] for p in ids
        ]

    def make_test_match(self, home_key: str, away_key: str,
                        start_time: datetime, result: bool = True,
                        home_score: int = 2, away_score: int = 1):
        home_id = self.teams[home_key][M_ID]
        away_id = self.teams[away_key][M_ID]
        # Selections are player ids.
        selections = self.user_ids_list(PLAYER_ROLE, [home_key, away_key])
        match = MatchData(
            0, home_id, away_id, start_time, result, home_score, away_score,
            selections)
        return match, home_id, away_id, selections

    def test_create_match(self):
        """ Test create a match """
        index = 0
        for user in UserType:
            with self.subTest(user=user):
                permissions = self.set_permissions(user)
                index = index + 1

                new_match, _, _, _ = self.make_test_match(
                    TEAM_1, TEAM_2,
                    datetime(2021, 5, index, 10 + index, 45),   # May 1,2 etc.
                    home_score=1 * index, away_score=2 * index  # 1-2, 2-4 etc.
                )
                has = BaseTestCase.has_permission(
                    permissions, POST_MATCH_PERMISSION)
                expect = Expect.SUCCESS if has else Expect.FAILURE
                if has:
                    http_status = HTTPStatus.OK
                else:
                    http_status = HTTPStatus.UNAUTHORIZED

                MatchesTestCase.create_match(
                    self, expect, new_match, users=self.users,
                    http_status=http_status)

    def modified_copy(self, match: dict, index: MatchAttribMods, valid: bool,
                      home_id: int = 0, away_id: int = 0,
                      other_id: int = 0,
                      other_time: datetime = datetime.now(),
                      other_selections=None
                      ) -> tuple[dict, str]:
        """
        Create a modified copy of the specified match.
        :param match:    match to copy
        :param index:    index of attribute to modify
        :param valid:    attribute validity flag
        :param home_id:  valid home id
        :param away_id:  valid away id
        :param other_id: valid other team id
        :param other_time: valid==True - valid time,
                           valid==False - conflict time
        :param other_selections: valid other selections
        :return:
        """
        if other_selections is None:
            other_selections = []
        mod_match = deepcopy(match)
        if valid and index not in HAVE_VALID_CHANGES:
            # Set unique start time so valid test will pass.
            mod_match[M_START_TIME] = \
                mod_match[M_START_TIME] + timedelta(days=int(index))
        if index == MatchAttribMods.HOME_TEAM:
            if valid:
                mod_match[M_HOME_ID] = home_id
                info = "valid home_id"
            else:
                mod_match[M_HOME_ID] = 0
                info = "invalid home_id"
        elif index == MatchAttribMods.AWAY_TEAM:
            if valid:
                mod_match[M_AWAY_ID] = away_id
                info = "valid away_id"
            else:
                mod_match[M_AWAY_ID] = 0
                info = "invalid away_id"
        elif index == MatchAttribMods.SCORE_HOME:
            if valid:
                mod_match[M_SCORE_HOME] = 3
                info = "valid score_home"
            else:
                mod_match[M_SCORE_HOME] = -1
                info = "invalid score_home"
        elif index == MatchAttribMods.SCORE_AWAY:
            if valid:
                mod_match[M_SCORE_AWAY] = 3
                info = "valid score_away"
            else:
                mod_match[M_SCORE_AWAY] = -1
                info = "invalid score_away"
        elif index == MatchAttribMods.START_TIME:
            mod_match[M_START_TIME] = other_time
            if valid:
                info = "valid start_time"
            else:
                info = "invalid start_time conflict"
        elif index == MatchAttribMods.SELECTIONS:
            if valid:
                mod_match[M_SELECTIONS] = \
                    self.user_ids_list(PLAYER_ROLE, other_selections)
                info = "valid selections"
            else:
                mod_match[M_SELECTIONS] = [1000, 1001]
                info = "invalid selections"
        elif index == MatchAttribMods.DUPLICATE_TEAM_CONFLICT:
            if valid:
                mod_match[M_HOME_ID] = home_id
                mod_match[M_AWAY_ID] = away_id
                info = "valid match team home/away"
            else:
                mod_match[M_HOME_ID] = home_id
                mod_match[M_AWAY_ID] = home_id
                info = "conflict match team home/away"
        elif index == MatchAttribMods.DUPLICATE_MATCH_CONFLICT:
            mod_match[M_HOME_ID] = home_id
            mod_match[M_AWAY_ID] = away_id
            if valid:
                info = "valid match teams/time"
            else:
                info = "conflict match teams/time"
        elif index == MatchAttribMods.HOME_CONFLICT:
            mod_match[M_HOME_ID] = home_id
            mod_match[M_AWAY_ID] = other_id
            if valid:
                info = "valid match home fixture"
            else:
                info = "conflict home fixture"
        elif index == MatchAttribMods.AWAY_CONFLICT:
            mod_match[M_HOME_ID] = other_id
            mod_match[M_AWAY_ID] = away_id
            if valid:
                info = "valid match away fixture"
            else:
                info = "conflict away fixture"
        elif index == MatchAttribMods.HOME_AWAY_CONFLICT:
            mod_match[M_HOME_ID] = other_id
            mod_match[M_AWAY_ID] = home_id
            if valid:
                info = "valid match home team away fixture"
            else:
                info = "conflict home team away fixture"
        elif index == MatchAttribMods.AWAY_HOME_CONFLICT:
            mod_match[M_HOME_ID] = away_id
            mod_match[M_AWAY_ID] = other_id
            if valid:
                info = "valid match away team home fixture"
            else:
                info = "conflict away home team fixture"
        else:
            self.fail(f"Unexpected index {index}")

        return mod_match, info

    def test_create_invalid_match(self):
        """ Test creating an invalid match """
        self.set_permissions(UserType.MANAGER)

        ok_match, home_id, away_id, selections = self.make_test_match(
            TEAM_1, TEAM_2,
            datetime(2021, 6, 1, 15, 15))
        ok_match = MatchesTestCase.create_match(
            self, Expect.SUCCESS, ok_match, users=self.users)

        other_time = datetime(2021, 6, 1, 19, 30)
        other_match, _, _, _ = \
            self.make_test_match(TEAM_1, TEAM_3, other_time)
        other_match = MatchesTestCase.create_match(
            self, Expect.SUCCESS, other_match, users=self.users)

        ok_match_template = deepcopy(ok_match)
        ok_match_template[M_SELECTIONS] = selections

        for index in MatchAttribMods:
            with self.subTest(index=index):
                bad_match, info = self.modified_copy(
                    ok_match_template, index, False,
                    home_id=home_id, away_id=away_id,
                    other_id=self.teams[TEAM_3][M_ID],
                    other_time=other_time, other_selections=[TEAM_4, TEAM_5]
                )

                MatchesTestCase.create_match(
                    self, Expect.FAILURE, bad_match, users=self.users,
                    http_status=range(400, 500), tag=f'index {index} {info}')

    def _delete_match(self, expect: Expect, match_id: int,
                      http_status: Union[HTTPStatus, range] = HTTPStatus.OK):
        """
        Create a match
        :param expect:   Expected result; one of Expect.SUCCESS or
                         Expect.FAILURE
        """
        msg = f'match_id {match_id}'
        with self.client as client:
            resp = client.delete(
                make_url(MATCH_BY_ID_URL, match_id=match_id)
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

    def test_delete_match(self):
        """ Test deleting a match """
        for user in UserType:
            with self.subTest(user=user):
                permissions = self.set_permissions(user)

                has = BaseTestCase.has_permission(
                    permissions, POST_MATCH_PERMISSION)
                if has:
                    new_match, _, _, _ = self.make_test_match(
                        TEAM_1, TEAM_2,
                        datetime(2021, 7, 1, 16, 16))

                    # Create match to delete
                    to_delete = MatchesTestCase.create_match(
                        self, Expect.SUCCESS, new_match, users=self.users)
                    delete_id = to_delete[M_ID]
                else:
                    delete_id = 1  # Arbitrary id, should not have access.

                has = BaseTestCase.has_permission(
                    permissions, DELETE_MATCH_PERMISSION)
                expect = Expect.SUCCESS if has else Expect.FAILURE
                if has:
                    http_status = HTTPStatus.OK
                else:
                    http_status = HTTPStatus.UNAUTHORIZED

                self._delete_match(expect, delete_id, http_status=http_status)

    def test_delete_invalid_match(self):
        """ Test deleting an invalid match """
        self.set_permissions(UserType.MANAGER)

        self._delete_match(Expect.FAILURE, 1000,
                           http_status=HTTPStatus.NOT_FOUND)

    def _update_match(self, expect: Expect, match_id: int, old_match: dict,
                      new_match: dict, tag: str,
                      http_status: Union[HTTPStatus, range] = HTTPStatus.OK):
        """
        Update a match
        :param expect:   Expected result; one of Expect.SUCCESS or
                         Expect.FAILURE
        """
        updates = {}
        for k, v in old_match.items():
            new_v = new_match[k]
            if new_v != v:
                updates[k] = new_v

        msg = f'match_id {match_id} {old_match} -> {new_match} = {updates} ' \
              f'{tag if tag is not None else ""}'
        with self.client as client:
            resp = client.patch(
                make_url(MATCH_BY_ID_URL, match_id=match_id), json=updates
            )

            resp_body = json.loads(resp.data)
            if expect == Expect.SUCCESS:
                expected = self.standardise_match(new_match)
                # Set selections to player dicts.
                selections = expected[M_SELECTIONS]
                if len(selections) > 0 and isinstance(selections[0], int):
                    expected[M_SELECTIONS] = [
                        MatchesTestCase.find_user(self, self.users, uid)
                        for uid in selections
                    ]

                self.assert_ok(resp.status_code, msg=msg)
                self.assert_success_response(resp_body, msg=msg)
                self.assert_body_entry(resp_body, RESULT_UPDATED_COUNT,
                                       MatchParam.EQUAL, value=1, msg=msg)
                self.assert_body_entry(resp_body, RESULT_ONE_MATCH,
                                       MatchParam.EQUAL, value=expected,
                                       msg=msg)
            else:
                if isinstance(http_status, HTTPStatus):
                    self.assert_response_status_code(http_status,
                                                     resp.status_code, msg=msg)

                self.assertTrue(resp.is_json)
                self.assert_error_response(resp_body, http_status, '',
                                           MatchParam.IGNORE, msg=msg)

    def test_update_match(self):
        """ Test updating a match """
        self.set_permissions(UserType.MANAGER)

        # Create match which will not change.
        no_change_match, home_id, away_id, selections = \
            self.make_test_match(
                TEAM_1, TEAM_2,
                datetime(2021, 8, 1, 17, 17))
        no_change_match = MatchesTestCase.create_match(
            self, Expect.SUCCESS, no_change_match, users=self.users)

        for user in UserType:
            with self.subTest(user=user):
                permissions = self.set_permissions(user)

                old_time = datetime(2021, 8, 2, 17, 17)
                new_time = datetime(2021, 8, 3, 18, 18)

                has = BaseTestCase.has_permission(
                    permissions, POST_MATCH_PERMISSION)
                if has:
                    old_match, home_id, away_id, selections = \
                        self.make_test_match(TEAM_1, TEAM_2, old_time)
                    # Create match to update
                    old_match = MatchesTestCase.create_match(
                        self, Expect.SUCCESS, old_match, users=self.users)
                else:
                    old_match = no_change_match

                has = BaseTestCase.has_permission(
                    permissions, PATCH_MATCH_PERMISSION)
                expect = Expect.SUCCESS if has else Expect.FAILURE
                if has:
                    if old_match is None:
                        self.fail("No match to update")
                    http_status = HTTPStatus.OK
                else:
                    http_status = HTTPStatus.UNAUTHORIZED

                count = 0
                for index in HAVE_VALID_CHANGES:
                    if count > 0 and http_status != HTTPStatus.OK:
                        # Does not have permission, so only need to test once.
                        continue
                    count = count + 1

                    with self.subTest(index=index):
                        mod_match, info = self.modified_copy(
                            old_match, index, True,
                            home_id=self.teams[TEAM_4][M_ID],
                            away_id=self.teams[TEAM_5][M_ID],
                            other_id=self.teams[TEAM_3][M_ID],
                            other_time=new_time,
                            other_selections=[TEAM_4, TEAM_5]
                        )

                        self._update_match(expect, old_match[M_ID],
                                           old_match, mod_match, info,
                                           http_status=http_status)
                        old_match = mod_match

    def test_update_match_invalid(self):
        """ Test updating a match """
        permissions = self.set_permissions(UserType.MANAGER)

        has = BaseTestCase.has_permission(
            permissions, POST_MATCH_PERMISSION)
        if has:
            # Create previously scheduled match.
            other_time = datetime(2021, 9, 1, 21, 15)
            other_match, _, _, _ = \
                self.make_test_match(TEAM_1, TEAM_3, other_time)
            other_match = MatchesTestCase.create_match(
                self, Expect.SUCCESS, other_match, users=self.users)

            # Create match to try to modify.
            no_mod_time = datetime(2021, 9, 2, 22, 00)
            no_mod_match, home_id, away_id, selections = \
                self.make_test_match(
                    TEAM_1, TEAM_2, no_mod_time)
            no_mod_match = MatchesTestCase.create_match(
                self, Expect.SUCCESS, no_mod_match, users=self.users)
        else:
            self.fail("Could not create match")

        has = BaseTestCase.has_permission(
            permissions, PATCH_MATCH_PERMISSION)
        if has:
            if no_mod_match is None:
                self.fail("No match to update")
            http_status = range(400, 500)
        else:
            self.fail("No match update permission")

        count = 0
        for index in MatchAttribMods:
            if count > 0 and http_status != HTTPStatus.OK:
                # Does not have permission, so only need to test once.
                continue
            count = count + 1

            with self.subTest(index=index):
                mod_match, info = self.modified_copy(
                    no_mod_match, index, False,
                    home_id=self.teams[TEAM_4][M_ID],
                    away_id=self.teams[TEAM_5][M_ID],
                    other_id=self.teams[TEAM_3][M_ID],
                    other_time=other_time
                )

                self._update_match(Expect.FAILURE, no_mod_match[M_ID],
                                   no_mod_match, mod_match, info,
                                   http_status=http_status)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
