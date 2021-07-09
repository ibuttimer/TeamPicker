from sqlalchemy import and_
from sqlalchemy.orm import scoped_session

from ..constants import RESULT_UPDATED_COUNT, RESULT_ONE_USER
from ..models import db_session, ResultType, User
from .base_service import get_all, get_by_id, exists_by_id, create_entity, \
    delete_by_id, update_entity, get_by_id_raw, get_one


def get_all_users(result_type: ResultType = ResultType.DICT):
    """
    Get all users.
    :param result_type: type of result required, one of ResultType
    :return: list of all users.
    """
    return get_all(User, result_type=result_type)


def get_user_by_id(user_id: int, result_type: ResultType = ResultType.DICT):
    """
    Get a user.
    :param user_id: id of user to get
    :param result_type: type of result required, one of ResultType
    :return: user
    """
    return get_by_id(User, user_id, result_type=result_type)


def get_user_by_id_raw(session: scoped_session, user_id: int):
    """
    Get a user.
    :param session:
    :param user_id: id of user to get
    :return: user
    """
    return get_by_id_raw(session, User, user_id)


def user_exists(user_id: int):
    """
    Check if a user exists by id.
    :param user_id:     id of user to check
    :return: True if exists otherwise False
    """
    return exists_by_id(User, user_id)


def get_user_by_auth0_id(auth0_id: str,
                         result_type: ResultType = ResultType.DICT):
    """
    Get a user by auth0_id.
    :param auth0_id:    auth0_id of user to get
    :param result_type: type of result required, one of ResultType
    :return: user
    """
    return get_one(User, criteria=User.auth0_id == auth0_id,
                   result_type=result_type)


def get_users_by_role_and_team(role_id: int, team_id: int,
                               result_type: ResultType = ResultType.DICT):
    """
    Get users by role & team.
    :param role_id:    role id of users to get
    :param team_id:    team id of users to get
    :param result_type: type of result required, one of ResultType
    :return: users
    """
    return get_all(User,
                   criteria=and_(
                       User.role_id == role_id, User.team_id == team_id),
                   result_type=result_type)


def create_user(entity: dict, result_type: ResultType = ResultType.DICT):
    """
    Create a user.
    :param entity:      entity value dict
    :param result_type: type of result required, one of ResultType
    :return: created result {
        "created": <number of affected entities>,
        "id": <id of new entity>
        "user": <new entity>
    }
    """
    return create_entity(User.from_dict, entity, RESULT_ONE_USER,
                         result_type=result_type)


def delete_user_by_id(user_id: int):
    """
    Delete a user by id.
    :param user_id: id of user to delete
    :return: deleted result {
        "deleted": <number of affected entities>
    }
    """
    return delete_by_id(User, user_id)


def update_user(user_id: int, updates: dict,
                result_type: ResultType = ResultType.DICT):
    """
    Update a user.
    :param user_id:     id of user to update
    :param updates:     updates to apply
    :param result_type: type of result required, one of ResultType
    :return: updated result {
        "updated": <number of affected entities>,
        "user": <updated entity>
    }
    """
    result = update_entity(User,
                           User.is_valid_entity(updates,
                                                attribs=updates.keys()),
                           criteria=User.id == user_id)
    if result[RESULT_UPDATED_COUNT] > 0:
        result[RESULT_ONE_USER] = get_user_by_id(
            user_id, result_type=result_type)

    return result
