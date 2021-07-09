import unittest
from http import HTTPStatus

from flask import Response

from team_picker.constants import (ROLES_URL, RESULT_LIST_ROLES, ROLE_BY_ID_URL,
                                   RESULT_ONE_ROLE, GET_ROLE_PERMISSION
                                   )

from base_test import BaseTestCase
from misc import make_url, MatchParam, UserType
from test_data import EqualDataMixin, ROLES


class RolesTestCase(BaseTestCase):
    """This class represents the test case for roles."""

    def setUp(self):
        """
        Method called to prepare the test fixture.
        This is called immediately before calling the test method.
        """
        super().setUp()

    def assert_role(self, expected: EqualDataMixin, actual: dict,
                    msg: str = None):
        """
        Assert roles are equal.
        """
        if msg is None:
            msg = ""
        self.assert_equal_data(expected, actual, ignore=None)

    def tearDown(self):
        """
        Method called immediately after the test method has been called
        and the result recorded.
        """
        super().tearDown()

    def assert_roles_list(self, expected: list[EqualDataMixin], actual: list,
                          msg: str = None):
        """
        Assert roles lists are equal.
        """
        if msg is None:
            msg = ""
        self.assertEqual(len(expected), len(actual),
                         f'Length mismatch for {msg}')
        index = 0
        for actual_drink in actual:
            with self.subTest(actual_drink=actual_drink):
                self.assert_role(expected[index], actual_drink,
                                 msg=f'drink {index} {msg}')
                index = index + 1

    def assert_roles_list_resp(self, expected: list[EqualDataMixin],
                               resp: Response, msg: str = None):
        """
        Assert roles list responses are equal.
        """
        if msg is None:
            msg = ""

        self.assert_ok(resp.status_code)

        self.assertTrue(resp.is_json)
        resp_body = resp.get_json()

        self.assert_success_response(resp_body)
        self.assert_body_entry(resp_body, RESULT_LIST_ROLES, MatchParam.IGNORE)
        resp_roles = resp_body[RESULT_LIST_ROLES]

        self.assert_roles_list(expected, resp_roles, msg=msg)

    def assert_role_resp(self, expected: EqualDataMixin, resp: Response,
                         msg: str = None):
        """
        Assert roles list responses are equal.
        """
        if msg is None:
            msg = ""

        self.assert_ok(resp.status_code)

        self.assertTrue(resp.is_json)
        resp_body = resp.get_json()

        self.assert_success_response(resp_body)
        self.assert_body_entry(resp_body, RESULT_ONE_ROLE, MatchParam.EQUAL,
                               value=expected)

    def test_get_all_roles(self):
        """
        Test get all roles.
        """
        for user in UserType:
            permissions = self.set_permissions(user)

            with self.subTest(user=user):
                with self.client as client:
                    resp = client.get(
                        make_url(ROLES_URL)
                    )

                if permissions is None or \
                        GET_ROLE_PERMISSION not in permissions:
                    self.assert_unauthorized_request(resp.status_code)
                else:
                    self.assert_roles_list_resp(
                        [v for k, v in ROLES.items()], resp)

    def test_get_role_by_id(self):
        """
        Test get roles by id.
        """
        for user in UserType:
            permissions = self.set_permissions(user)

            with self.subTest(user=user):
                for k, v in ROLES.items():
                    with self.subTest(role=v):
                        with self.client as client:
                            resp = client.get(
                                make_url(ROLE_BY_ID_URL, role_id=v.id)
                            )

                        if permissions is None or \
                                GET_ROLE_PERMISSION not in permissions:
                            self.assert_unauthorized_request(resp.status_code)
                        else:
                            self.assert_role_resp(v.to_dict(), resp)

    def test_get_role_by_invalid_id(self):
        """
        Test get role by an invalid id.
        """
        for user in UserType:
            permissions = self.set_permissions(user)

            with self.subTest(user=user):
                with self.client as client:
                    resp = client.get(
                        make_url(ROLE_BY_ID_URL, role_id=1000)
                    )

                http_status = HTTPStatus.UNAUTHORIZED \
                    if permissions is None or \
                    GET_ROLE_PERMISSION not in permissions \
                    else HTTPStatus.NOT_FOUND

                self.assert_response_status_code(http_status,
                                                 resp.status_code)

                self.assertTrue(resp.is_json)
                self.assert_error_response(resp.get_json(),
                                           http_status.value,
                                           http_status.phrase,
                                           MatchParam.CASE_INSENSITIVE,
                                           MatchParam.IN)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
