import json
import pathlib
import unittest
from http import HTTPStatus

from bs4 import BeautifulSoup

from base_test import BaseTestCase
from base_ui_test import UiBaseTestCase
from misc import make_url, UserType
from team_picker.constants import (USER_SETUP_URL,
                                   LOGIN_URL, TEAM_SETUP_URL,
                                   POST_TEAM_PERMISSION, SETUP_COMPLETE,
                                   DASHBOARD_URL, YES_ARG, NEW_TEAM_QUERY,
                                   SET_TEAM_QUERY, DB_ID,
                                   )
from team_picker.models import (M_ID, M_NAME, M_SURNAME, M_AUTH0_ID, M_ROLE_ID,
                                M_TEAM_ID
                                )
from team_picker.services import create_user
from test_data import (ROLES, UserData, MANAGER_ROLE,
                       PLAYER_ROLE, TeamData, get_role_from_id, UNASSIGNED_TEAM
                       )

MANAGERS_FILE = pathlib.Path(__file__).parent \
    .joinpath("postman", "managers.json")
PLAYERS_FILE = pathlib.Path(__file__).parent \
    .joinpath("postman", "players.json")


class UsersSetupTestCase(UiBaseTestCase):
    """This class represents the test case for user UI-related functionality."""

    users = {}
    teams = {}

    def setUp(self):
        """
        Method called to prepare the test fixture.
        This is called immediately before calling the test method.
        """
        super().setUp()

        # Read required users and teams.
        self.users, self.teams = UsersSetupTestCase.read_users_and_teams()

    @staticmethod
    def read_users_and_teams():
        """
        Read users and teams from file.
        :return tuple of users and teams
        """
        # Read required users and teams.
        # Only one team per manager, read teams from manager file.
        teams = UsersSetupTestCase.read_teams(MANAGERS_FILE)
        # Read managers.
        users = UsersSetupTestCase.read_users(
            MANAGERS_FILE, teams.keys(), MANAGER_ROLE)
        # Read players.
        users.update(UsersSetupTestCase.read_users(
            PLAYERS_FILE, teams.keys(), PLAYER_ROLE))

        return users, teams

    @staticmethod
    def read_teams(file):
        """
        Read teams from file (team's have only one manager, so create team for
        each manager).
        :param file: file to load
        :return a dict of the form {
            '<team_name>': TeamData(..),
            ..
        }
        """
        with file.open() as f:
            data = json.load(f)
            teams = {
                team["team_name"]: TeamData(0, team["team_name"])
                for team in data
            }
        return teams

    @staticmethod
    def user_key(role: str, index: int, team_name: str):
        """
        Generate a user key.
        :param role: role of user
        :param index: index of user
        :param team_name: name of user's team
        :return '<role>$<index>$<team_name>' e.g. 'manager$1$Team 1'
        """
        return f'{role}${index}${team_name}'

    @staticmethod
    def split_user_key(key: str):
        """
        Split a user key into its constitute parts.
        :param key: key to split
        :return tuple of role, index, team_name e.g. 'manager', '1' 'Team 1'
        """
        splits = key.split("$")
        return splits[0], splits[1], splits[2]

    @staticmethod
    def read_users(file, teams, role):
        """
        Read users from file.
        :param file: file to load
        :param teams: list of team names
        :param role: role of users
        :return a dict of the form {
            'role<idx>_<team_name>': UserData(..),
            ..
        }
        """
        counts = {k: 0 for k in teams}

        def get_count(team_name):
            counts[team_name] = counts[team_name] + 1
            return counts[team_name]

        with file.open() as f:
            data = json.load(f)
            users = {
                UsersSetupTestCase.user_key(
                    role, get_count(user["team_name"]), user["team_name"]):
                UserData(0, user["firstname"], user["surname"],
                         f'auth0|m_id_{user["username"]}',
                         ROLES[role].id, 0)
                for user in data
            }
        return users

    def tearDown(self):
        """
        Method called immediately after the test method has been called
        and the result recorded.
        """
        super().tearDown()

    def test_setup_user(self):
        """
        Test setup users; success for authorised users, otherwise failure.
        """
        with self.client as client:
            for _, user in self.users.items():

                with self.subTest(user=user):
                    role = get_role_from_id(user.role_id)

                    for user_type in [UserType.PUBLIC, UserType.UNAUTHORISED]:
                        with self.subTest(user_type=user_type):

                            permissions = self.set_permissions(
                                user_type, profile={
                                    M_NAME: user.name,
                                    M_AUTH0_ID: user.auth0_id,
                                    SETUP_COMPLETE: False
                                }, role=role
                            )
                            resp = client.post(
                                make_url(USER_SETUP_URL), data={
                                    M_NAME: user.name,
                                    M_SURNAME: user.surname,
                                    M_ROLE_ID: user.role_id
                                }
                            )

                            # Only authenticated users should be able to do
                            # setup, unauthenticated should redirect to login.
                            url = LOGIN_URL
                            if user_type == UserType.PUBLIC:
                                query = NEW_TEAM_QUERY \
                                    if role == MANAGER_ROLE else \
                                    (SET_TEAM_QUERY
                                     if role == PLAYER_ROLE else None)
                                if query is not None:
                                    url = make_url(DASHBOARD_URL, **{
                                        query: YES_ARG
                                    })

                            self.assert_response_status_code(
                                HTTPStatus.FOUND, resp.status_code)

                            soup = BeautifulSoup(resp.data, 'html.parser')

                            UiBaseTestCase.assert_redirect(self, soup, url)

                            # self.assertIn("Dashboard",
                            #               str(soup.title.string))
                            # # Check menu.
                            # self.assert_menu(soup,
                            #                  available=MENU_BASIC_ALL,
                            #                  not_available=MENU_MATCHES)
                            # # Check body; welcome message and form title.
                            # self.assert_tag_text(
                            #     soup, "h2#welcome_user", user.name,
                            #     match=MatchParam.IN)
                            # self.assert_tag_text(
                            #     soup, "h3[class=form-heading]",
                            #     "Create user", match=MatchParam.EQUAL)
                            # # Check user form.
                            # for selector in ["input#name",
                            #                  "input#surname",
                            #                  "select#role",
                            #                  "input[type=submit]"]:
                            #     self.assert_tag_exists(soup, selector)

    def test_manager_create_team(self):
        """
        Test only managers are able to create teams.
        """
        with self.app.app_context():
            with self.client as client:
                for key, user in self.users.items():
                    role, index, team_name = \
                        UsersSetupTestCase.split_user_key(key)

                    # Need to add user to database to perform test.
                    new_user = user.to_dict(ignore=[M_ID])
                    new_user[M_TEAM_ID] = UNASSIGNED_TEAM.id
                    created = create_user(new_user)

                    with self.subTest(user=user):

                        user_types = [
                            UserType.PUBLIC, UserType.UNAUTHORISED
                        ] + [
                            UserType.MANAGER
                            if user.role_id == ROLES[MANAGER_ROLE].id
                            else UserType.PLAYER
                        ]

                        for user_type in user_types:
                            with self.subTest(user_type=user_type):
                                permissions = self.set_permissions(
                                    user_type, profile={
                                        M_NAME: user.name,
                                        M_AUTH0_ID: user.auth0_id,
                                        SETUP_COMPLETE: False,
                                        DB_ID: created[M_ID]
                                    }, role=role)

                                resp = client.post(
                                    make_url(TEAM_SETUP_URL), json={
                                        M_NAME: team_name
                                    }
                                )

                                has = BaseTestCase.has_permission(
                                    permissions, POST_TEAM_PERMISSION)
                                if has:
                                    http_status = HTTPStatus.FOUND
                                    url = DASHBOARD_URL
                                elif user_type == UserType.PUBLIC or \
                                        user_type == UserType.PLAYER:
                                    http_status = HTTPStatus.UNAUTHORIZED
                                    url = None
                                else:
                                    http_status = HTTPStatus.FOUND
                                    url = LOGIN_URL

                                self.assert_response_status_code(
                                    http_status, resp.status_code)

                                soup = BeautifulSoup(resp.data, 'html.parser')

                                if http_status == HTTPStatus.FOUND:
                                    UiBaseTestCase.assert_redirect(self, soup, url)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
