from http import HTTPStatus

from flask import (abort, request, make_response
                   )

from ..auth.auth import requires_auth, AuthErrorMode
from ..constants import (POST_MATCH_PERMISSION, DELETE_MATCH_PERMISSION,
                         PATCH_MATCH_PERMISSION, GET_MATCH_PERMISSION,
                         RESULT_ONE_MATCH, ORDER_QUERY
                         )
from ..models import (M_START_TIME
                      )
from ..services import (get_all_matches, get_match_by_id as get_match_by_id_svc,
                        create_match as create_match_svc, delete_match_by_id,
                        update_match as update_match_svc, match_exists
                        )
from ..util import success_result
from ..util.exception import AbortError

POST_PATCH_PERMISSION = [POST_MATCH_PERMISSION, PATCH_MATCH_PERMISSION]
GET_POST_PATCH_PERMISSION = [POST_MATCH_PERMISSION, PATCH_MATCH_PERMISSION,
                             GET_MATCH_PERMISSION]


def standardise_match(match: dict) -> dict:
    """
    Standardise match in preparation for returning result.
    :param match: match to standardise
    :return:
    """
    # Transform start_time to iso format for transmission to client, otherwise
    # standard JSON encoder produces RFC1123 format.
    match[M_START_TIME] = match[M_START_TIME].isoformat()
    return match


def standardise_match_list(match_list: list[dict]) -> list[dict]:
    """
    Standardise match list in preparation for returning result.
    :param match_list: matches to standardise
    :return:
    """
    for match in match_list:
        standardise_match(match)
    return match_list


@requires_auth(GET_MATCH_PERMISSION, mode=AuthErrorMode.EXCEPTION)
def all_matches_api(payload: dict):
    """
    Get all matches via API endpoint.
    :param payload: JWT payload
    :return:
    """
    match_list = get_all_matches(
        order_by=request.args.get(ORDER_QUERY, None, type=str))

    return success_result(
        matches=standardise_match_list(match_list)
    )


@requires_auth(GET_MATCH_PERMISSION, mode=AuthErrorMode.EXCEPTION)
def get_match_by_id_api(payload: dict, match_id: int):
    """
    Get a match.
    :param payload: JWT payload
    :param match_id: id of match to get
    :return:
    """
    match = get_match_by_id_svc(match_id)
    if match is None:
        abort(HTTPStatus.NOT_FOUND)

    return success_result(
        match=standardise_match(match)
    )


@requires_auth(POST_MATCH_PERMISSION, mode=AuthErrorMode.EXCEPTION)
def create_match_api(payload: dict):
    """
    Create a match.
    :param payload: JWT payload
    :return:
    """
    if not request.json:
        raise AbortError(HTTPStatus.BAD_REQUEST,
                         "Malformed request, expecting JSON.")

    created = create_match_svc(request.get_json())
    created[RESULT_ONE_MATCH] = standardise_match(created[RESULT_ONE_MATCH])

    return make_response(
        success_result(**created), HTTPStatus.CREATED)


def delete_match_impl(match_id: int):
    """
    Delete a match.
    :param match_id: id of match to delete
    :return:
    """
    if not match_exists(match_id):
        abort(HTTPStatus.NOT_FOUND)
    deleted = delete_match_by_id(match_id)

    return make_response(
        success_result(**deleted), HTTPStatus.OK)


@requires_auth(DELETE_MATCH_PERMISSION, mode=AuthErrorMode.EXCEPTION)
def delete_match_api(payload: dict, match_id: int):
    """
    Delete a match via API endpoint.
    :param payload: JWT payload
    :param match_id: id of match to delete
    :return:
    """
    return delete_match_impl(match_id)


@requires_auth(PATCH_MATCH_PERMISSION, mode=AuthErrorMode.EXCEPTION)
def update_match_api(payload: dict, match_id: int):
    """
    Update a match via API endpoint.
    :param payload: JWT payload
    :param match_id: id of match to delete
    :return:
    """
    if not match_exists(match_id):
        abort(HTTPStatus.NOT_FOUND)
    if not request.json:
        raise AbortError(HTTPStatus.BAD_REQUEST,
                         "Malformed request, expecting JSON.")

    updated = update_match_svc(match_id, request.get_json())
    updated[RESULT_ONE_MATCH] = standardise_match(updated[RESULT_ONE_MATCH])

    return make_response(
        success_result(**updated), HTTPStatus.OK)


