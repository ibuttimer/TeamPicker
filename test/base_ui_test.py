from typing import Optional, List

from base_test import BaseTestCase, AUTH_PATH, PERMISSIONS_BY_ROLE, \
    SERVER_SESSION_PATH
from misc import MatchParam, UserType
from team_picker.constants import *
from team_picker.models import M_ROLE, M_ROLE_ID, M_NAME, M_AUTH0_ID, M_TEAM_ID


class MenuItem(Enum):
    HOME = "menu_home"
    MATCHES = "menu_matches"
    MATCH_LIST = "menu_match_list"
    MATCH_SEARCH = "menu_match_search"
    MATCH_NEW = "menu_match_new"
    LOGOUT = "menu_logout"


MENU_BASIC_ALL = [MenuItem.HOME, MenuItem.LOGOUT]
MENU_BASIC_NA = [v for v in MenuItem if v not in MENU_BASIC_ALL]
MENU_MANAGER_NA = []
MENU_MANAGER_ALL = [v for v in MenuItem]
MENU_PLAYER_NA = [MenuItem.MATCH_NEW]
MENU_PLAYER_ALL = [v for v in MenuItem if v not in MENU_PLAYER_NA]
MENU_MATCHES_VIEW = [MenuItem.MATCH_LIST, MenuItem.MATCH_SEARCH]
MENU_MATCHES_CREATE = [MenuItem.MATCH_NEW]
MENU_MATCHES = MENU_MATCHES_VIEW + MENU_MATCHES_CREATE


APP_MODULE = 'team_picker'
CONTROLLER_MODULE = f'{APP_MODULE}.controllers'
USER_CONTROLLER_PATH = f'{CONTROLLER_MODULE}.user_controller'

CHECK_SETUP_COMPLETE = "check_setup_complete"
IS_LOGGED_IN = "is_logged_in"
IS_LOGGED_IN_APP_KEY = "is_logged_in_app_module"
SESSION_PROFILE = "session_profile"
ADD_USER_ROLE = "add_user_role"
GET_ROLE_PERMISSIONS = "get_role_permissions"
GET_PROFILE_SETUP_COMPLETE = "get_profile_setup_complete"


class UiBaseTestCase(BaseTestCase):
    """This is the base class for all UI-related test cases."""

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)

        # Mock functions.
        # NOTE: Need to patch where an object is looked up, which is not
        #       necessarily the same place as where it is defined.
        # https://docs.python.org/3/library/unittest.mock.html#where-to-patch
        # E.g. for the case of is_logged_in() it needs to be mocked in where
        # it is defined, as its used in that module, and also in the app
        # module as its also used there.
        patchers = [(k, f'{USER_CONTROLLER_PATH}.{k}')
                    for k in [ADD_USER_ROLE, GET_ROLE_PERMISSIONS]] + \
                   [(k, f'{AUTH_PATH}.{k}')
                    for k in
                    [IS_LOGGED_IN, CHECK_SETUP_COMPLETE,
                     GET_PROFILE_SETUP_COMPLETE]] + \
                   [(k, f'{SERVER_SESSION_PATH}.{k}')
                    for k in [SESSION_PROFILE]] + \
                   [(IS_LOGGED_IN_APP_KEY, f'{APP_MODULE}.{IS_LOGGED_IN}')]

        for key, target in patchers:
            self.setup_patcher(key, target)

    def setup_mocks(self):
        super().setup_mocks()

        # Configure the mock return values.
        for key in [
            IS_LOGGED_IN, IS_LOGGED_IN_APP_KEY, CHECK_SETUP_COMPLETE,
            GET_PROFILE_SETUP_COMPLETE
        ]:
            self.mocker.get(key).return_value = False
        self.mocker.get(SESSION_PROFILE).return_value = {}
        self.mocker.get(ADD_USER_ROLE).return_value = {}
        self.mocker.get(GET_ROLE_PERMISSIONS).return_value = []

    def set_permissions(self, user_type: UserType, profile: dict = None,
                        role: str = '') -> Optional[List[str]]:
        jwt_permissions, role_id, role = \
            BaseTestCase.get_permissions_and_role(user_type, role=role)

        logged_in = (jwt_permissions is not None)
        for key in [IS_LOGGED_IN, IS_LOGGED_IN_APP_KEY]:
            self.mocker.get(key).return_value = logged_in

        if jwt_permissions is None:
            mock_profile = None
            setup_complete = False
        else:
            mock_profile = {
                M_ROLE_ID: role_id,
                M_ROLE: role,
                MANAGER_ROLE: (role == MANAGER_ROLE),
                PLAYER_ROLE: (role == PLAYER_ROLE)
            }
            if profile is None:
                # Possible entries;
                # M_NAME, SETUP_COMPLETE, M_AUTH0_ID, DB_ID, M_TEAM_ID
                profile = {
                    M_NAME: '',
                    M_AUTH0_ID: '',
                    SETUP_COMPLETE: False,
                    DB_ID: 0,
                    M_TEAM_ID: 0
                }
            mock_profile.update(profile)
            setup_complete = profile[SETUP_COMPLETE]
        self.mocker.get(SESSION_PROFILE).return_value = mock_profile
        self.mocker.get(CHECK_SETUP_COMPLETE).return_value = setup_complete

        self.mocker.get(ADD_USER_ROLE).return_value = {M_ROLE: role}
        self.mocker.get(GET_ROLE_PERMISSIONS).return_value = \
            None if user_type == UserType.UNAUTHORISED else \
            (PERMISSIONS_BY_ROLE[role]
             if role in PERMISSIONS_BY_ROLE.keys() else [])
        self.mocker.get(GET_PROFILE_SETUP_COMPLETE).return_value = \
            setup_complete if logged_in else False

        return super().set_permissions(user_type, profile, role)

    @staticmethod
    def assert_menu(testcase: BaseTestCase, soup, available: list = None,
                    not_available: list = None):
        """
        Assert the page menu is correct.
        :param testcase: test case
        :param soup: BeautifulSoup object
        :param available: list of required available menu items
        :param not_available: list of required unavailable menu items
        """
        # Test existence of menu items
        if available is not None:
            for item in available:
                testcase.assertEqual(1, len(soup.select(f"a#{item.value}")),
                                     msg=f'Menu item {item.value} not found')
        # Test non-existence of menu items
        if not_available is not None:
            for item in not_available:
                testcase.assertEqual(0, len(soup.select(f"a#{item.value}")),
                                     msg=f'Menu item {item.value} found')

    @staticmethod
    def assert_tag_exists(testcase: BaseTestCase, soup, selector: str,
                          count: int = 1) -> list:
        """
        Check that a tag exists in a html page.
        :param testcase: test case
        :param soup: BeautifulSoup object
        :param selector: tag selector
        :param count: number of tags to match
        :return: list of objects found
        """
        selected = soup.select(selector)
        testcase.assertEqual(count, len(selected),
                             msg=f"Tag item '{selector}' count mismatch: "
                                 f"found {len(selected)} != {count}")
        return selected

    @staticmethod
    def assert_tag_text(testcase: BaseTestCase, soup, selector: str,
                        expected: str = None, attribute: str = None,
                        match: MatchParam = MatchParam.EQUAL,
                        count: int = 1):
        """
        Check that a tag exists in a html page and verify it's text or
        attribute.
        Special attribute use cases:
        - check for non-existence of attribute using
          match=MatchParam.NOT_IN and expected=None
        :param testcase: test case
        :param soup: BeautifulSoup object
        :param selector: tag selector
        :param expected: expected text
        :param attribute: attribute of tag to check
        :param match: match criteria
        :param count: number of tags to match
        """
        selected = UiBaseTestCase.assert_tag_exists(
            testcase, soup, selector, count=count)
        for entry in selected:
            actual = None
            if attribute is None:
                actual = entry.string
                if actual is None and expected == "":
                    actual = expected
                else:
                    actual = str(actual)
            else:
                has = entry.has_attr(attribute)
                if match == MatchParam.NOT_IN and expected is None:
                    fail = "has" if has else None
                    if not has:
                        return  # Existence check complete.
                else:
                    fail = "does not have" if not has else None
                if fail is not None:
                    testcase.fail(
                        f"{selector} {has} attribute {attribute}")
                else:
                    actual = entry.get(attribute)

            if match == MatchParam.EQUAL:
                testcase.assertEqual(expected, actual)
            elif match == MatchParam.NOT_EQUAL:
                testcase.assertNotEqual(expected, actual)
            elif match == MatchParam.IN:
                testcase.assertIn(expected, actual)
            elif match == MatchParam.NOT_IN:
                testcase.assertNotIn(expected, actual)
            else:
                testcase.fail(f'Unimplemented match param: {match}')

    @staticmethod
    def assert_redirect(testcase: BaseTestCase, soup, url: str):
        """
        Check that a html page represents a redirect.
        :param testcase: test case
        :param soup: BeautifulSoup object
        :param url: expected redirect url
        """
        testcase.assertIn("Redirect", str(soup.title.string))
        testcase.assertEqual(url, soup.a.get('href'))
