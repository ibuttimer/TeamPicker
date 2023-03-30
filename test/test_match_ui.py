import pathlib
import random
import unittest
from collections import namedtuple
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Union, Optional, Any

from bs4 import BeautifulSoup
from flask import Response

from base_test import BaseTestCase
from base_ui_test import UiBaseTestCase, MENU_BASIC_ALL, MENU_MANAGER_ALL, \
    MENU_PLAYER_ALL, MENU_MANAGER_NA, MENU_PLAYER_NA, \
    MENU_BASIC_NA
from misc import make_url, MatchParam, UserType, Expect
from team_picker.constants import (LOGIN_URL, SETUP_COMPLETE,
                                   DASHBOARD_URL, YES_ARG, DB_ID,
                                   MATCHES_UI_URL,
                                   NEW_QUERY, POST_MATCH_PERMISSION, OPPOSITION,
                                   VENUE, TEAM_SCORE, OPPOSITION_SCORE,
                                   APP_DATETIME_FMT, GET_MATCH_PERMISSION,
                                   UPDATE_QUERY, MATCH_BY_ID_UI_URL,
                                   MATCH_ID_PARAM, ORDER_QUERY, ORDER_DATE_ASC,
                                   DELETE_MATCH_PERMISSION, SEARCH_QUERY,
                                   SEARCH_MATCH_URL, APP_DATE_FMT,
                                   MATCH_SELECTIONS_UI_URL,
                                   MATCH_USER_SELECTION_UI_URL, USER_ID_PARAM,
                                   MATCH_USER_CONFIRM_UI_URL,
                                   PATCH_OWN_MATCH_PERMISSION,
                                   )
from team_picker.models import (M_ID, M_NAME, M_AUTH0_ID, M_TEAM_ID,
                                M_START_TIME, M_RESULT, M_SCORE_AWAY,
                                M_SCORE_HOME, M_AWAY_ID, M_HOME_ID,
                                M_SELECTIONS, M_CONFIRMED
                                )
from team_picker.services import get_all_matches
from team_picker.util import HOME_VENUE, AWAY_VENUE, DateRange, \
    NO_OPTION_SELECTED, NO_STATUS, MAYBE_STATUS, NOT_AVAILABLE_STATUS, \
    CONFIRMED_STATUS
from test_data import (ROLES, UserData, MANAGER_ROLE,
                       PLAYER_ROLE, TeamData, get_role_from_id, MatchData,
                       ENTITY_ID
                       )
from test_matches import MatchesTestCase
from test_user_setup_ui import UsersSetupTestCase

MANAGERS_FILE = pathlib.Path(__file__).parent \
    .joinpath("postman", "managers.json")
PLAYERS_FILE = pathlib.Path(__file__).parent \
    .joinpath("postman", "players.json")

CodeUrl = namedtuple('CodeUrl', ['code', 'url'])

OK_NO_URL = CodeUrl(HTTPStatus.OK, None)
FOUND_LOGIN = CodeUrl(HTTPStatus.FOUND, LOGIN_URL)
FOUND_DASHBOARD = CodeUrl(HTTPStatus.FOUND, DASHBOARD_URL)
NOT_FOUND_NO_URL = CodeUrl(HTTPStatus.NOT_FOUND, None)
UNAUTHORISED_NO_URL = CodeUrl(HTTPStatus.UNAUTHORIZED, None)

# https://www.crummy.com/software/BeautifulSoup/bs4/doc/
# Match form selectors.
HOME_SELECTOR = "input#venue-0"  # Input with id venue-0.
AWAY_SELECTOR = "input#venue-1"
RESULT_SELECTOR = "input#result"
START_TIME_SELECTOR = "input#start_time"
TEAM_SCORE_SELECTOR = "input#team_score"
OPPOSITION_SCORE_SELECTOR = "input#opposition_score"
OPPOSITION_SELECTOR = "select#opposition"
SUBMIT_SELECTOR = "input[type=submit]"  # Input with type 'submit'.
# Selector is 'option tag with selected attribute below
# select tag with id opposition'
OPPOSITION_OPTION_SELECTOR = f"{OPPOSITION_SELECTOR} > " \
                             f"option[selected]"

# Search form selectors.
# Search form uses START_TIME_SELECTOR, OPPOSITION_SELECTOR & SUBMIT_SELECTOR
# selectors as well.
# Selector is 'option tag below select tag with id opposition'
SEARCH_OPPOSITION_OPTION_SELECTOR = f"{OPPOSITION_SELECTOR} > option"
# Selector is 'input tag below td tag with id beginning with date_range'
SEARCH_DATE_RANGE_OPTION_SELECTOR = f"td > input[id^='date_range']"

DATE_RANGE = "date_range"

# Match list selectors
SCORE = "score"
SELECTION = "selection"
EDIT = "edit"
DELETE = "delete"
MATCH_SELECTORS = {
    M_START_TIME: "td#start-time-%d",
    VENUE: "td#venue-%d",
    OPPOSITION: "td#opposition-%d",
    M_RESULT: "i#result-%d",
    SCORE: "td#score-%d",
    SELECTION: "a#match-selections-%d",
    EDIT: "a#edit-match-%d",
    DELETE: "button#delete-match-%d"
}

# Selections list selectors
TOGGLE_SELECT = "toggle-select"
CONFIRM = "Confirm"
UNSURE = "Unsure"
NOT_AVAILABLE = "Not available"
OTHER_SELECTION = "other-selection"
SELECTION_START_TIME_SELECTOR = "td#start-time"
SELECTION_VENUE_SELECTOR = "td#venue"
SELECTION_OPPOSITION_SELECTOR = "td#opposition"
SELECTIONS_SELECTORS = {
    M_NAME: "td#player-name-%d",
    TOGGLE_SELECT: "button#toggle-select-%d",  # Manager only.
    SELECTION: "i#select-status-%d",  # Manager only.
    CONFIRM: "input#toggle-confirm-y",  # Logged in player only.
    UNSURE: "input#toggle-confirm-m",  # Logged in player only.
    NOT_AVAILABLE: "input#toggle-confirm-n",  # Logged in player only.
    OTHER_SELECTION: "i#player-status-%d",  # Other users.
}

CONFIRMED_TEXTS = {
    NO_STATUS: "Not applicable",
    NOT_AVAILABLE_STATUS: "Not available",
    MAYBE_STATUS: "Unconfirmed",
    CONFIRMED_STATUS: "Confirmed"
}


def select_selector(testcase: UiBaseTestCase, selectors: dict, key: str,
                    index: Optional[int]):
    if key not in selectors.keys():
        testcase.fail(f"Unknown selector {key}")
    return selectors[key] % index if index is not None else selectors[key]


def match_selector(testcase: UiBaseTestCase, key: str, index: Optional[int]):
    return select_selector(testcase, MATCH_SELECTORS, key, index)


def selections_selector(testcase: UiBaseTestCase, key: str, index:
                        Optional[int]):
    return select_selector(testcase, SELECTIONS_SELECTORS, key, index)


class TestMatchUiCase(UiBaseTestCase):
    """
    This class represents the test case for match UI-related
    functionality.

    TODO Remove test duplication in some test loops.
    """

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

        # Persist users and teams and teams to database.
        with self.app.app_context():
            app_db = self.get_db()
            for _, team_data in self.teams.items():
                team = team_data.to_model(ignore=[M_ID])
                app_db.session.add(team)
                app_db.session.flush()
                team_data.id = team.id

            for key, user_data in self.users.items():
                role, index, team_name = UsersSetupTestCase.split_user_key(key)

                user = user_data.to_model(ignore=[M_ID])
                user.team_id = self.teams.get(team_name).id
                app_db.session.add(user)
                app_db.session.flush()
                user_data.id = user.id
                user_data.team_id = user.team_id

            app_db.session.commit()

        self.user_dicts = {v.id: v.to_dict() for _, v in self.users.items()}

    def tearDown(self):
        """
        Method called immediately after the test method has been called
        and the result recorded.
        """
        super().tearDown()

    def get_opposition(self, team_id: int, exclude=None) -> TeamData:
        """
        Get an opposition team.
        :param team_id: id of team to get opposition for
        :param exclude: team ids to exclude
        :return: opposition TeamData()
        """
        if exclude is None:
            exclude = []
        for team_key, team_data in self.teams.items():
            if team_data.id != team_id and team_data.id not in exclude:
                opposition = team_data
                break
        else:
            self.fail(f"Opposition not found for {team_id}")
        return opposition

    def get_team(self, team_id: int):
        """
        Get a team.
        :param team_id: id of team to get
        :return: team TeamData()
        """
        for team_key, team_data in self.teams.items():
            if team_data.id == team_id:
                team = team_data
                break
        else:
            self.fail(f"Team not found: {team_id}")
        return team

    @staticmethod
    def create_match_dict(venue: int, opposition: Union[int, TeamData],
                          start_time: datetime, result: bool = False,
                          team_score: int = 0, opposition_score: int = 0,
                          selections: list = None) -> dict:
        """
        Generate match dict for create/update match form data.
        :param venue:
        :param opposition:
        :param start_time:
        :param result:
        :param team_score:
        :param opposition_score:
        :param selections:
        :return:
        """
        if selections is None:
            selections = []
        return {
            VENUE: venue,
            OPPOSITION:
                opposition if isinstance(opposition, int) else opposition.id,
            M_START_TIME: start_time.strftime(APP_DATETIME_FMT),
            M_RESULT: result,
            TEAM_SCORE: team_score,
            OPPOSITION_SCORE: opposition_score,
            M_SELECTIONS: [
                s if isinstance(s, int) else s.id for s in selections]
        }

    @staticmethod
    def search_match_dict(opposition: Union[int, TeamData] = NO_OPTION_SELECTED,
                          start_time: datetime = datetime.now(),
                          date_range: DateRange = DateRange.IGNORE_DATE
                          ) -> dict:
        """
        Generate match dict for create/update match form data.
        :param opposition:
        :param start_time:
        :param date_range:
        :return:
        """
        return {
            OPPOSITION:
                opposition if isinstance(opposition, int) else opposition.id,
            M_START_TIME: start_time.strftime(APP_DATE_FMT),
            DATE_RANGE: str(date_range)
        }

    def set_permissions_and_profile(self, user: UserData, user_type: UserType,
                                    role: str, permission: str,
                                    has_and: bool = True,
                                    has_code: CodeUrl = OK_NO_URL,
                                    has_not_and_code:
                                    CodeUrl = NOT_FOUND_NO_URL,
                                    unauthorised: list[UserType] = None,
                                    else_code: CodeUrl = FOUND_LOGIN):
        """
        Set user permissions for test.
        :param user: user data
        :param user_type: user type
        :param role: user role
        :param permission: permission to check that the user has
        :param has_and: additional 'and' condition for has test
        :param has_code: status code and url (if applicable) to expect if user 
                         has permission and has_and condition
        :param has_not_and_code: status code and url (if applicable) to expect 
                         if user has permission but not has_and condition
        :param unauthorised: list of user types which expect unauthorised
                             status code
        :param else_code: status code and url (if applicable) to expect if no
                         other test satisfied
        :return tuple of user permissions, expected status code, redirect url
        """
        if unauthorised is None:
            unauthorised = [UserType.PUBLIC, UserType.PLAYER]

        permissions = self.set_permissions(
            user_type, profile={
                M_NAME: user.name,
                M_AUTH0_ID: user.auth0_id,
                SETUP_COMPLETE: True,
                DB_ID: user.id,
                M_TEAM_ID: user.team_id
            }, role=role
        )

        has = BaseTestCase.has_permission(permissions, permission)
        if has and has_and:
            code_url = has_code
        elif has and not has_and:
            code_url = has_not_and_code
        elif user_type in unauthorised:
            code_url = UNAUTHORISED_NO_URL
        else:
            code_url = else_code

        http_status = code_url.code
        url = code_url.url

        return permissions, http_status, url \
            if http_status == HTTPStatus.FOUND else None

    def assert_status_and_redirect(self, resp: Response,
                                   http_status: HTTPStatus,
                                   url: str = None) -> BeautifulSoup:
        """
        Check response status code and redirect if applicable
        :param resp: server response
        :param http_status: status code
        :param url: url for redirect
        :return BeautifulSoup of response
        """
        self.assert_response_status_code(
            http_status, resp.status_code)

        soup = BeautifulSoup(resp.data, 'html.parser')

        if http_status == HTTPStatus.FOUND:
            # Check redirect.
            UiBaseTestCase.assert_redirect(self, soup, url)

        return soup

    def assert_page_form(self, resp: Response, http_status: HTTPStatus,
                         title: str, user_type: UserType,
                         url: str = None) -> tuple[BeautifulSoup, HTTPStatus]:
        """
        Check if a page form is correct.
        :param resp: server response
        :param http_status: status code
        :param title: expected title
        :param user_type: type of user to test menu for
        :param url: url for redirect
        """
        soup = self.assert_status_and_redirect(resp, http_status, url=url)

        if http_status == HTTPStatus.OK:
            # Check new form.
            self.assertIn(title, str(soup.title.string))
            # Check menu.
            menu = {'available': MENU_MANAGER_ALL,
                    'not_available': MENU_MANAGER_NA} \
                if user_type == UserType.MANAGER else \
                ({'available': MENU_PLAYER_ALL,
                  'not_available': MENU_PLAYER_NA}
                 if user_type == UserType.PLAYER else
                 {'available': MENU_BASIC_ALL,
                  'not_available': MENU_BASIC_NA})

            UiBaseTestCase.assert_menu(self, soup, **menu)
            # Check body.
            UiBaseTestCase.assert_tag_text(
                self, soup, "h3[class=form-heading]",
                expected=title, match=MatchParam.EQUAL)

        return soup, http_status

    def assert_match_form(self, resp: Response, http_status: HTTPStatus,
                          title: str, user_type: UserType,
                          match: MatchData = None, team_id: int = None,
                          url: str = None):
        """
        Check if a match form is correct.
        :param resp: server response
        :param http_status: status code
        :param title: expected title
        :param user_type: type of user to test menu for
        :param match: match data to verify
        :param team_id: team id of user
        :param url: url for redirect
        """
        soup, http_status = self.assert_page_form(
            resp, http_status, title, user_type, url=url)

        if http_status == HTTPStatus.OK:
            if match is not None and team_id is not None:
                # Verify match data.
                is_home = (match.home_id == team_id)
                # Check correct radio input has checked attribute.
                UiBaseTestCase.assert_tag_text(
                    self, soup, HOME_SELECTOR if is_home else AWAY_SELECTOR,
                    expected="", attribute="checked", match=MatchParam.EQUAL)
                # Check result checkbox input has checked attribute if result
                # final.
                args = {'expected': "", 'match': MatchParam.EQUAL} \
                    if match.result else \
                    {'expected': None, 'match': MatchParam.NOT_IN}
                UiBaseTestCase.assert_tag_text(
                    self, soup, RESULT_SELECTOR, attribute="checked", **args
                )
                # Check start time and scores.
                for selector, expected in [
                    (START_TIME_SELECTOR, match.strf_start_time()),
                    (TEAM_SCORE_SELECTOR,
                     str(match.score_home if is_home else match.score_away)),
                    (OPPOSITION_SCORE_SELECTOR,
                     str(match.score_away if is_home else match.score_home))
                ]:
                    UiBaseTestCase.assert_tag_text(
                        self, soup, selector, expected=expected,
                        attribute="value", match=MatchParam.EQUAL)
                # Check opposition.
                UiBaseTestCase.assert_tag_text(
                    self, soup, OPPOSITION_OPTION_SELECTOR,
                    expected=str(match.away_id if is_home else match.home_id),
                    attribute="value", match=MatchParam.EQUAL)
            else:
                # Verify existence of tags.
                for selector in [HOME_SELECTOR, AWAY_SELECTOR, RESULT_SELECTOR,
                                 START_TIME_SELECTOR, TEAM_SCORE_SELECTOR,
                                 OPPOSITION_SCORE_SELECTOR,
                                 OPPOSITION_SELECTOR]:
                    UiBaseTestCase.assert_tag_exists(self, soup, selector)

            # Verify existence of submit tag.
            UiBaseTestCase.assert_tag_exists(self, soup, SUBMIT_SELECTOR)

    def assert_search_form(self, resp: Response, http_status: HTTPStatus,
                           title: str, user_type: UserType,
                           url: str = None):
        """
        Check if a search form is correct.
        :param resp: server response
        :param http_status: status code
        :param title: expected title
        :param user_type: type of user to test menu for
        :param url: url for redirect
        """
        soup, http_status = self.assert_page_form(
            resp, http_status, title, user_type, url=url)

        if http_status == HTTPStatus.OK:
            # Verify existence of tags.
            for selector in [START_TIME_SELECTOR, OPPOSITION_SELECTOR]:
                UiBaseTestCase.assert_tag_exists(self, soup, selector)

            UiBaseTestCase.assert_tag_exists(
                self, soup, SEARCH_OPPOSITION_OPTION_SELECTOR,
                # All teams except one plus 'select' option
                count=len(self.teams.keys()))

            UiBaseTestCase.assert_tag_exists(
                self, soup, SEARCH_DATE_RANGE_OPTION_SELECTOR,
                count=len([d.value for d in DateRange]))

            # Verify existence of submit tag.
            UiBaseTestCase.assert_tag_exists(self, soup, SUBMIT_SELECTOR)

        return soup, http_status

    @staticmethod
    def is_manager(user: UserData):
        return user.role_id == ROLES[MANAGER_ROLE].id

    @staticmethod
    def is_player(user: UserData):
        return user.role_id == ROLES[PLAYER_ROLE].id

    @staticmethod
    def get_user_type(user: UserData):
        return UserType.MANAGER \
            if user.role_id == ROLES[MANAGER_ROLE].id else \
            (UserType.PLAYER
             if user.role_id == ROLES[PLAYER_ROLE].id
             else UserType.UNAUTHORISED)

    @staticmethod
    def user_type_generator(user: UserData):
        for user_type in [UserType.PUBLIC, UserType.UNAUTHORISED,
                          TestMatchUiCase.get_user_type(user)]:
            yield user_type

    # @unittest.skip
    def test_create_match(self):
        """
        Test only managers can create matches, and other users are redirected
        or rejected as appropriate.
        """
        delta = timedelta()
        for key, user in self.users.items():
            role, index, team_name = UsersSetupTestCase.split_user_key(key)
            delta = delta + timedelta(days=1)

            with self.subTest(user=user):
                role = get_role_from_id(user.role_id)

                for user_type in self.user_type_generator(user):
                    with self.subTest(user_type=user_type):
                        with self.client as client:
                            # First verify the initial get of the match form.
                            permissions, http_status, url = \
                                self.set_permissions_and_profile(
                                    user, user_type, role,
                                    POST_MATCH_PERMISSION,
                                    unauthorised=[UserType.PUBLIC,
                                                  UserType.PLAYER]
                                )

                            resp = client.get(
                                make_url(MATCHES_UI_URL, **{NEW_QUERY: YES_ARG})
                            )

                            self.assert_match_form(
                                resp, http_status, "New match", user_type,
                                url=url)

                            if http_status != HTTPStatus.OK:
                                continue  # Finished if don't have access.

                            # Else test match creation.
                            # (Just do valid case as invalid cases are tested in
                            # API tests in test_matches.py)

                            resp = client.post(
                                make_url(MATCHES_UI_URL),
                                data=TestMatchUiCase.create_match_dict(
                                    HOME_VENUE,
                                    self.get_opposition(user.team_id),
                                    (datetime.now() + delta),
                                    result=True,
                                    team_score=1, opposition_score=2
                                ))

                            self.assert_status_and_redirect(
                                resp, HTTPStatus.FOUND, url=DASHBOARD_URL)

    @staticmethod
    def pick_players(players: dict, team: int):
        return random.sample(
            players[team][M_ID], k=int(len(players[team][M_ID]) / 2))

    def generate_test_matches(self, iterations: int = 1) -> list[MatchData]:
        """
        Generate a list of test matches.
        :param  iterations: number of iterations (one match against each other
                            team) to perform
        :return tuple of list of MatchData matches and players
        """
        # Create matches to test with.
        delta = timedelta()
        test_matches = []  # List of created matches.
        count = 0

        # Generate player lists of user ids.
        players = {}
        for key, user in self.users.items():
            role, index, team_name = UsersSetupTestCase.split_user_key(key)
            if role == PLAYER_ROLE:
                # Use team id as key.
                team_id = self.teams[team_name].id
                if team_id not in players.keys():
                    players[team_id] = {PLAYER_ROLE: [], M_ID: []}

                players[team_id][PLAYER_ROLE].append(user)
                players[team_id][M_ID].append(user.id)

        # Generate matches
        for key, user in self.users.items():
            role, index, team_name = UsersSetupTestCase.split_user_key(key)
            if role == MANAGER_ROLE:
                permissions = self.set_permissions(
                    UserType.MANAGER, profile={
                        M_NAME: user.name,
                        M_AUTH0_ID: user.auth0_id,
                        SETUP_COMPLETE: True,
                        DB_ID: user.id,
                        M_TEAM_ID: user.team_id
                    }, role=role
                )

                for _ in range(iterations):
                    for team_key, team_data in self.teams.items():
                        if team_data.id == user.team_id:
                            continue

                        delta = delta + timedelta(days=1)
                        count = count + 1

                        def by_mod2(one, zero):
                            return one if count % 2 else zero

                        match_data = {
                            ENTITY_ID: 0,
                            M_HOME_ID: by_mod2(user.team_id, team_data.id),
                            M_AWAY_ID: by_mod2(team_data.id, user.team_id),
                            M_START_TIME: (datetime.now() + delta),
                            M_RESULT: by_mod2(True, False),
                            M_SCORE_HOME: (1 * count),
                            M_SCORE_AWAY: (2 * count),
                            M_SELECTIONS:
                                self.pick_players(players, user.team_id) +
                                self.pick_players(players, team_data.id)
                        }
                        new_match = MatchData(**match_data)
                        created = MatchesTestCase.create_match(
                            self, Expect.SUCCESS, new_match,
                            users=self.user_dicts)
                        new_match.id = created[M_ID]
                        new_match.selections = created[M_SELECTIONS]

                        # Add created match to list.
                        test_matches.append(new_match)

        return test_matches, players

    def generate_match_listing(self, user: UserData,
                               test_matches: list[MatchData]) -> list[dict]:
        """
        Generate match list as it should appear in UI, (it's different for each
        user depending on their team).
        :param user: user to generate listing for
        :param test_matches: match list
        :return:
        """

        def by_id(match_data: MatchData, home_val, away_val):
            return home_val \
                if match_data.home_id == user.team_id \
                else away_val

        def by_field(match_data: dict, home_fld, away_fld):
            return match_data[
                home_fld
                if match_data[M_HOME_ID] == user.team_id
                else away_fld]

        # Generate match list as it should appear in UI, (it's
        # different for each user depending on their team).
        ui_matches = []
        for match in test_matches:
            if match.home_id != user.team_id and match.away_id != user.team_id:
                # Not playing, so don't have access
                continue

            match_dict = match.to_dict()
            team_score = \
                by_field(match_dict, M_SCORE_HOME, M_SCORE_AWAY)
            opposition_score = \
                by_field(match_dict, M_SCORE_AWAY, M_SCORE_HOME)
            ui_matches.append({
                M_START_TIME: match.strf_start_time(),
                VENUE: by_id(match, "Home", "Away"),
                OPPOSITION:
                    self.get_team(
                        by_field(
                            match_dict, M_AWAY_ID, M_HOME_ID)
                    ).name,
                M_RESULT:
                    ("Win" if team_score > opposition_score else
                     ("Loss"
                      if team_score < opposition_score
                      else "Draw"))
                    if match.result else "Result not final",
                SCORE:
                    f"{match.score_home} - {match.score_away}"
                    if match.result else ""
            })
        return ui_matches

    def assert_matches_list(self, user: UserData, user_type: UserType,
                            test_matches: list[MatchData],
                            criteria: dict = None) -> BeautifulSoup:
        """
        Get list matches and verify details.
        """
        role = get_role_from_id(user.role_id)
        is_manager = TestMatchUiCase.is_manager(user)
        is_player = TestMatchUiCase.is_player(user)

        permissions, http_status, url = \
            self.set_permissions_and_profile(
                user, user_type, role, GET_MATCH_PERMISSION
            )

        with self.client as client:
            if criteria is None:
                # Get all matches.
                resp = client.get(
                    make_url(MATCHES_UI_URL, **{ORDER_QUERY: ORDER_DATE_ASC})
                )
                title = 'Matches'
            else:
                # Search matches
                resp = client.post(
                    make_url(SEARCH_MATCH_URL, **{ORDER_QUERY: ORDER_DATE_ASC}),
                    data=criteria
                )
                title = 'Match search results'

        soup = self.assert_status_and_redirect(resp, http_status, url=url)

        if http_status == HTTPStatus.OK:
            # Generate match list as it should appear in UI, (it's
            # different for each user depending on their team).
            ui_matches = self.generate_match_listing(user, test_matches)

            # Check listing.
            self.assertEqual(title, str(soup.title.string))
            # Check menu.
            UiBaseTestCase.assert_menu(
                self, soup,
                available=(MENU_MANAGER_ALL if is_manager else MENU_PLAYER_ALL),
                not_available=(MENU_MANAGER_NA
                               if is_manager else MENU_PLAYER_NA),
            )
            # Check body.
            index = -1
            for match in ui_matches:
                with self.subTest(match=match):
                    index = index + 1
                    for selector, attribute in [
                        (M_START_TIME, None), (VENUE, None),
                        (OPPOSITION, None), (M_RESULT, "title"),
                        (SCORE, None),
                    ]:
                        UiBaseTestCase.assert_tag_text(
                            self, soup,
                            match_selector(self, selector, index),
                            expected=match[selector],
                            attribute=attribute, match=MatchParam.EQUAL)

                    button_list = [match_selector(self, SELECTION, index)]
                    if is_manager:
                        # Additional buttons for manager.
                        button_list = button_list + [
                            match_selector(self, EDIT, index),
                            match_selector(self, DELETE, index)
                        ]
                    for selector in button_list:
                        UiBaseTestCase.assert_tag_exists(self, soup, selector)
        return soup

    # @unittest.skip
    def test_list_matches(self):
        """
        Test only managers and players can list matches, and other users are
        redirected or rejected as appropriate.
        """
        # Create matches to test with.
        test_matches, _ = self.generate_test_matches()

        # Check match listings.
        for key, user in self.users.items():
            with self.subTest(user=user):
                for user_type in self.user_type_generator(user):
                    with self.subTest(user_type=user_type):
                        # Verify matches listed correctly.
                        self.assert_matches_list(user, user_type, test_matches)

    @staticmethod
    def team_is_playing(team: Union[int, UserData], match: MatchData):
        team_id = team.team_id if isinstance(team, UserData) else team
        return team_id == match.home_id or team_id == match.away_id

    # @unittest.skip
    def test_update_matches(self):
        """
        Test only managers can update matches, and other users are
        redirected or rejected as appropriate.
        """
        self.context_wrapper(self.check_update_matches)

    def check_update_matches(self):
        """
        Test only managers can update matches, and other users are
        redirected or rejected as appropriate.
        """
        # Create matches to test with.
        test_matches, players = self.generate_test_matches()

        # Check match listings.
        first = True
        for key, user in self.users.items():
            with self.subTest(user=user):
                role = get_role_from_id(user.role_id)

                for user_type in self.user_type_generator(user):
                    with self.subTest(user_type=user_type):
                        with self.client as client:

                            if not first:
                                # Get the latest versions of matches from
                                # database.
                                test_matches = [MatchData.from_dict(m)
                                                for m in get_all_matches()]
                            first = False

                            for match in test_matches:
                                with self.subTest(match=match):
                                    # First verify the initial get of the match
                                    # form.
                                    is_playing = \
                                        self.team_is_playing(user, match)

                                    permissions, http_status, url = \
                                        self.set_permissions_and_profile(
                                            user, user_type, role,
                                            GET_MATCH_PERMISSION,
                                            has_and=is_playing
                                        )

                                    resp = client.get(
                                        make_url(MATCH_BY_ID_UI_URL, **{
                                            MATCH_ID_PARAM: match.id,
                                            UPDATE_QUERY: YES_ARG
                                        })
                                    )

                                    self.assert_match_form(
                                        resp, http_status, "Update match",
                                        user_type, match=match,
                                        team_id=user.team_id, url=url)

                                    # Update match.
                                    else_code = FOUND_LOGIN
                                    if user_type == UserType.PLAYER:
                                        else_code = \
                                            UNAUTHORISED_NO_URL if is_playing \
                                            else NOT_FOUND_NO_URL
                                    permissions, http_status, url = \
                                        self.set_permissions_and_profile(
                                            user, user_type, role,
                                            POST_MATCH_PERMISSION,
                                            has_code=FOUND_DASHBOARD,
                                            has_and=is_playing,
                                            unauthorised=[UserType.PUBLIC],
                                            else_code=else_code
                                        )

                                    # (Just do valid case as invalid cases are
                                    # tested in API tests in test_matches.py)
                                    is_home = (match.home_id == user.team_id)
                                    opposition = self.get_opposition(
                                        user.team_id, exclude=[
                                            match.away_id if is_home
                                            else match.home_id
                                        ])

                                    update = TestMatchUiCase.create_match_dict(
                                        AWAY_VENUE if is_home else
                                        HOME_VENUE,
                                        opposition,
                                        (match.start_time + timedelta(
                                            weeks=1)),
                                        result=not match.result,
                                        team_score=match.score_home + 10,
                                        opposition_score=(
                                                match.score_away + 10),
                                        # TODO persist selections via UI update
                                        # endpoint
                                        selections=
                                        self.pick_players(players,
                                                          user.team_id) +
                                        self.pick_players(players,
                                                          opposition.id)
                                    )
                                    resp = client.patch(
                                        make_url(MATCH_BY_ID_UI_URL, **{
                                            MATCH_ID_PARAM: match.id}),
                                        data=update)

                                    self.assert_status_and_redirect(
                                        resp, http_status, url=url)

    # @unittest.skip
    def test_delete_matches(self):
        """
        Test only managers can delete matches, and other users are
        redirected or rejected as appropriate.
        """
        # Create matches to test with.
        test_matches, _ = self.generate_test_matches(iterations=2)

        # Check match listings.
        with self.app.app_context():
            first = True
            for key, user in self.users.items():
                with self.subTest(user=user):
                    role = get_role_from_id(user.role_id)

                    for user_type in UserType:
                        with self.subTest(user_type=user_type):

                            if not first:
                                # Get the latest versions of matches from
                                # database.
                                test_matches = [MatchData.from_dict(m)
                                                for m in get_all_matches()]
                            first = False

                            for match in test_matches:
                                if self.team_is_playing(user, match):
                                    to_delete = match
                                    break
                            else:
                                self.fail("No match found to delete")

                            with self.subTest(match=to_delete):

                                permissions, http_status, url = \
                                    self.set_permissions_and_profile(
                                        user, user_type, role,
                                        DELETE_MATCH_PERMISSION
                                    )

                                with self.client as client:
                                    resp = client.delete(
                                        make_url(MATCH_BY_ID_UI_URL, **{
                                            MATCH_ID_PARAM: to_delete.id
                                        })
                                    )

                                self.assert_status_and_redirect(
                                    resp, http_status, url=url)

    # @unittest.skip
    def test_search_matches(self):
        """
        Test only managers and players can search matches, and other users are
        redirected or rejected as appropriate.
        """
        # Create matches to test with.
        test_matches, _ = self.generate_test_matches()

        # Check match listings.
        for key, user in self.users.items():
            role = get_role_from_id(user.role_id)

            with self.subTest(user=user):
                for user_type in self.user_type_generator(user):
                    with self.subTest(user_type=user_type):
                        # First verify the initial get of the search form.
                        permissions, http_status, url = \
                            self.set_permissions_and_profile(
                                user, user_type, role,
                                GET_MATCH_PERMISSION
                            )

                        with self.client as client:
                            resp = client.get(
                                make_url(MATCHES_UI_URL,
                                         **{SEARCH_QUERY: YES_ARG})
                            )

                        soup, http_status = self.assert_search_form(
                            resp, http_status, "Search match", user_type,
                            url=url)

                        if http_status != HTTPStatus.OK:
                            continue  # No more tests.

                        min_date = datetime.max.date()
                        max_date = datetime.min.date()
                        for match in test_matches:
                            match_date = match.start_time.date()
                            if match_date < min_date:
                                min_date = match_date
                            elif match_date > max_date:
                                max_date = match_date
                        min_date_plus_2 = min_date + timedelta(days=2)

                        for search in [OPPOSITION] + [
                            d for d in DateRange if d != DateRange.IGNORE_DATE
                        ]:
                            with self.subTest(search=search):
                                kwargs = {
                                    OPPOSITION: NO_OPTION_SELECTED,
                                    M_START_TIME: datetime.now(),
                                    DATE_RANGE: DateRange.IGNORE_DATE
                                }
                                search_matches = []
                                for match in test_matches:
                                    if not self.team_is_playing(user, match):
                                        continue

                                    if search == OPPOSITION:
                                        # Verify results based on opposition
                                        # search.
                                        if kwargs[OPPOSITION] == \
                                                NO_OPTION_SELECTED:
                                            kwargs[OPPOSITION] = \
                                                match.away_id \
                                                if user.team_id == \
                                                match.home_id \
                                                else match.home_id

                                        if self.team_is_playing(
                                                kwargs[OPPOSITION], match):
                                            search_matches.append(match)

                                    elif search == DateRange.BEFORE_DATE:
                                        # Verify results based on before date
                                        # search.
                                        kwargs[M_START_TIME] = min_date_plus_2
                                        kwargs[DATE_RANGE] = search
                                        if match.start_time.date() < \
                                                kwargs[M_START_TIME]:
                                            search_matches.append(match)
                                    elif search == \
                                            DateRange.BEFORE_OR_EQUAL_DATE:
                                        # Verify results based on before or
                                        # equal date search.
                                        kwargs[M_START_TIME] = min_date_plus_2
                                        kwargs[DATE_RANGE] = search
                                        if match.start_time.date() <= \
                                                kwargs[M_START_TIME]:
                                            search_matches.append(match)
                                    elif search == \
                                            DateRange.EQUAL_DATE:
                                        # Verify results based on equal date
                                        # search.
                                        kwargs[M_START_TIME] = min_date
                                        kwargs[DATE_RANGE] = search
                                        if match.start_time.date() == \
                                                kwargs[M_START_TIME]:
                                            search_matches.append(match)
                                    elif search == \
                                            DateRange.AFTER_OR_EQUAL_DATE:
                                        # Verify results based on after or
                                        # equal date search.
                                        kwargs[M_START_TIME] = min_date_plus_2
                                        kwargs[DATE_RANGE] = search
                                        if match.start_time.date() >= \
                                                kwargs[M_START_TIME]:
                                            search_matches.append(match)
                                    elif search == \
                                            DateRange.AFTER_DATE:
                                        # Verify results based on after date
                                        # search.
                                        kwargs[M_START_TIME] = min_date_plus_2
                                        kwargs[DATE_RANGE] = search
                                        if match.start_time.date() > \
                                                kwargs[M_START_TIME]:
                                            search_matches.append(match)

                                # Verify matches listed correctly.
                                self.assert_matches_list(
                                    user, user_type, search_matches,
                                    criteria=TestMatchUiCase.search_match_dict(
                                        **kwargs)
                                )

    def assert_selections_list(self, user: UserData, user_type: UserType,
                               match: MatchData, players: dict,
                               confirmed: dict = None) \
            -> tuple[BeautifulSoup, Any]:
        """
        Get match selections and verify details.
        """
        role = get_role_from_id(user.role_id)
        is_manager = TestMatchUiCase.is_manager(user)
        is_player = TestMatchUiCase.is_player(user)

        permissions, http_status, url = \
            self.set_permissions_and_profile(
                user, user_type, role,
                GET_MATCH_PERMISSION,
                has_and=(user.team_id == match.home_id or
                         user.team_id == match.away_id),
                has_not_and_code=NOT_FOUND_NO_URL
            )

        with self.client as client:
            # Get match selections.
            resp = client.get(
                make_url(MATCH_SELECTIONS_UI_URL, **{MATCH_ID_PARAM: match.id})
            )
            title = 'Match selections'

        soup = self.assert_status_and_redirect(resp, http_status, url=url)

        if http_status == HTTPStatus.OK:

            if confirmed is None:
                confirmed = {}

            selection_ids = [p[M_ID] for p in match.selections]
            all_players = [{
                M_ID: p.id,
                M_NAME: f"{p.name} {p.surname}",
                SELECTION: p.id in selection_ids,
                M_CONFIRMED: CONFIRMED_TEXTS[
                    NO_STATUS if p.id not in selection_ids else (
                        MAYBE_STATUS if p.id not in confirmed.keys()
                        else confirmed[p.id])
                ]
            } for p in players[user.team_id][PLAYER_ROLE]
            ]
            all_players.sort(key=lambda p: p[M_ID])
            # Check listing.
            self.assertEqual(title, str(soup.title.string))
            # Check menu.
            UiBaseTestCase.assert_menu(
                self, soup,
                available=(MENU_MANAGER_ALL if is_manager else MENU_PLAYER_ALL),
                not_available=(MENU_MANAGER_NA
                               if is_manager else MENU_PLAYER_NA),
            )
            # Check body.
            index = -1
            for player in all_players:
                with self.subTest(match=match):
                    index = index + 1

                    UiBaseTestCase.assert_tag_text(
                        self, soup,
                        selections_selector(self, M_NAME, index),
                        expected=player[M_NAME], match=MatchParam.EQUAL)
                    if is_manager:
                        # Verify set selection available.
                        UiBaseTestCase.assert_tag_exists(
                            self, soup,
                            selections_selector(self, TOGGLE_SELECT, index))
                        UiBaseTestCase.assert_tag_text(
                            self, soup,
                            selections_selector(self, SELECTION, index),
                            expected="Selected"
                            if player[SELECTION] else "Not Selected",
                            attribute="title", match=MatchParam.EQUAL)
                    elif player[M_ID] == user.id and player[SELECTION]:
                        # Verify player set confirmation available.
                        for selector, attribute in [
                            (CONFIRM, None), (UNSURE, None),
                            (NOT_AVAILABLE, None),
                        ]:
                            UiBaseTestCase.assert_tag_exists(
                                self, soup,
                                selections_selector(self, selector, None))
                    else:
                        # Verify others can only view status.
                        UiBaseTestCase.assert_tag_text(
                            self, soup,
                            selections_selector(self, OTHER_SELECTION, index),
                            expected=player[M_CONFIRMED],
                            attribute="title", match=MatchParam.EQUAL)

        return soup, http_status

    # @unittest.skip
    def test_get_match_selections(self):
        """
        Test only managers and players can get match selections and other users
        are redirected or rejected as appropriate.
        """
        # Create matches to test with.
        test_matches, players = self.generate_test_matches()

        # Check match listings.
        for key, user in self.users.items():
            role = get_role_from_id(user.role_id)

            with self.subTest(user=user):
                for user_type in self.user_type_generator(user):
                    with self.subTest(user_type=user_type):
                        for match in test_matches:
                            with self.subTest(match=match):
                                # First verify the initial get of the
                                # selections.
                                soup, http_status = self.assert_selections_list(
                                    user, user_type, match, players)

    # @unittest.skip
    def test_update_match_selections(self):
        """
        Test only managers can update match selections and other users
        are redirected or rejected as appropriate.
        """
        # Create matches to test with.
        test_matches, players = self.generate_test_matches()

        # Check match listings.
        for key, user in self.users.items():
            role = get_role_from_id(user.role_id)
            is_manager = TestMatchUiCase.is_manager(user)

            with self.subTest(user=user):
                for user_type in self.user_type_generator(user):
                    with self.subTest(user_type=user_type):
                        count = 0
                        for match in test_matches:
                            if count > 0 and \
                                    user_type in [UserType.PUBLIC,
                                                  UserType.UNAUTHORISED]:
                                continue  # No need to repeat test
                            count = count + 1

                            with self.subTest(match=match):
                                # Verify the change selection status of a
                                # player (only managers can do it).
                                permissions, http_status, url = \
                                    self.set_permissions_and_profile(
                                        user, user_type, role,
                                        POST_MATCH_PERMISSION,
                                        has_code=CodeUrl(
                                            HTTPStatus.FOUND,
                                            make_url(
                                                MATCH_SELECTIONS_UI_URL, **{
                                                    MATCH_ID_PARAM: match.id})
                                        ),
                                        has_and=(is_manager and
                                                 (user.team_id == match.home_id
                                                  or
                                                  user.team_id == match.away_id)
                                                 ),
                                        has_not_and_code=NOT_FOUND_NO_URL
                                    )

                                for player in match.selections:
                                    if player[M_TEAM_ID] == user.team_id:
                                        player_id = player[M_ID]
                                        break
                                else:
                                    if len(match.selections) > 0:
                                        # Doesn't matter as manager's team not
                                        # playing.
                                        player_id = match.selections[0][M_ID]
                                    else:
                                        self.fail("Cannot find player to "
                                                  "change selection")

                                with self.client as client:
                                    resp = client.post(
                                        make_url(MATCH_USER_SELECTION_UI_URL,
                                                 **{
                                                     MATCH_ID_PARAM: match.id,
                                                     USER_ID_PARAM: player_id
                                                 })
                                    )

                                self.assert_status_and_redirect(
                                    resp, http_status, url=url)

    # @unittest.skip
    def test_update_match_confirmations(self):
        """
        Test only players can update match confirmations and other users
        are redirected or rejected as appropriate.
        """
        # Create matches to test with.
        test_matches, players = self.generate_test_matches()

        # Check match listings.
        for key, user in self.users.items():
            role = get_role_from_id(user.role_id)
            is_player = TestMatchUiCase.is_player(user)

            with self.subTest(user=user):
                for user_type in self.user_type_generator(user):
                    with self.subTest(user_type=user_type):
                        count = 0
                        for match in test_matches:
                            if count > 0 and \
                                    user_type in [UserType.PUBLIC, 
                                                  UserType.UNAUTHORISED]:
                                continue  # No need to repeat test
                            count = count + 1

                            with self.subTest(match=match):
                                # Verify the change confirmation status of a
                                # player (only the player can do it).
                                for player in match.selections:
                                    if player[M_ID] == user.id and is_player:
                                        player_id = player[M_ID]
                                        break
                                else:
                                    if len(match.selections) > 0:
                                        # Doesn't matter as should not have
                                        # access.
                                        player_id = 0
                                    else:
                                        self.fail("Cannot find player to "
                                                  "confirm status")

                                permissions, http_status, url = \
                                    self.set_permissions_and_profile(
                                        user, user_type, role,
                                        PATCH_OWN_MATCH_PERMISSION,
                                        has_code=CodeUrl(
                                            HTTPStatus.FOUND,
                                            make_url(
                                                MATCH_SELECTIONS_UI_URL, **{
                                                    MATCH_ID_PARAM: match.id})
                                        ),
                                        has_and=((user.id == player_id)
                                                 and is_player),
                                        has_not_and_code=NOT_FOUND_NO_URL
                                    )

                                with self.client as client:
                                    resp = client.post(
                                        make_url(MATCH_USER_CONFIRM_UI_URL,
                                                 **{
                                                     MATCH_ID_PARAM: match.id,
                                                     USER_ID_PARAM: player_id
                                                 })
                                    )

                                self.assert_status_and_redirect(
                                    resp, http_status, url=url)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
