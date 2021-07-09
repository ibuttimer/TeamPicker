from http import HTTPStatus

from flask import abort

from ..auth.auth import requires_auth, AuthErrorMode
from ..constants import GET_ROLE_PERMISSION
from ..services import get_all_roles, get_role_by_id as get_role_by_id_svc
from ..util import success_result


@requires_auth(GET_ROLE_PERMISSION, mode=AuthErrorMode.EXCEPTION)
def all_roles(payload: dict):
    """
    Get all roles.
    :param payload: JWT payload
    :return:
    """
    roles = get_all_roles()

    return success_result(
        roles=roles
    )


@requires_auth(GET_ROLE_PERMISSION, mode=AuthErrorMode.EXCEPTION)
def get_role_by_id(payload: dict, role_id: int):
    """
    Get a role.
    :param payload: JWT payload
    :param role_id: id of role to get
    :return:
    """
    role = get_role_by_id_svc(role_id)
    if role is None:
        abort(HTTPStatus.NOT_FOUND)

    return success_result(
        role=role
    )
