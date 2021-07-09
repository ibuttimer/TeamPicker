from sqlalchemy import func

from ..constants import MANAGER_ROLE, PLAYER_ROLE, RESULT_ONE_ROLE
from ..models import ResultType, Role, M_ID
from .base_service import get_all, get_by_id, exists_by_id, get_one, \
    create_entity


def get_all_roles(result_type: ResultType = ResultType.DICT):
    """
    Get all roles.
    :param result_type: type of result required, one of ResultType
    :return: list of all roles.
    """
    return get_all(Role, result_type=result_type)


def get_role_by_id(role_id: int, result_type: ResultType = ResultType.DICT):
    """
    Get a role.
    :param role_id: id of role to get
    :param result_type: type of result required, one of ResultType
    :return: role
    """
    return get_by_id(Role, role_id, result_type=result_type)


def role_exists(role_id: int):
    """
    Check if a role exists by id.
    :param role_id:     id of role to check
    :return: True if exists otherwise False
    """
    return exists_by_id(Role, role_id)


def get_role_by_role(role: str, result_type: ResultType = ResultType.DICT):
    """
    Get a role.
    :param role: role to get
    :param result_type: type of result required, one of ResultType
    :return: role
    """
    return get_one(Role, criteria=func.lower(Role.role) == func.lower(role),
                   result_type=result_type)


def _is_role(role_id: int, role: str) -> bool:
    """
    Check if the specified role id represents the role.
    :param role_id: role id to check
    :param role: role to get
    :return: team
    """
    role_info = get_role_by_role(role)
    return role_id == role_info[M_ID]


def is_manager_role(role_id: int) -> bool:
    """
    Check if the specified role id represents the manager role.
    :param role_id: role id to check
    :return:
    """
    return _is_role(role_id, MANAGER_ROLE)


def is_player_role(role_id: int) -> bool:
    """
    Check if the specified role id represents the player role.
    :param role_id: role id to check
    :return:
    """
    return _is_role(role_id, PLAYER_ROLE)


def create_role(entity: dict, result_type: ResultType = ResultType.DICT):
    """
    Create a role.
    :param entity:      entity value dict
    :param result_type: type of result required, one of ResultType
    :return: created result {
        "created": <number of affected entities>,
        "id": <id of new entity>
        "role": <new entity>
    }
    """
    return create_entity(Role.from_dict, entity, RESULT_ONE_ROLE,
                         result_type=result_type)


