from http import HTTPStatus

from flask import abort, request, make_response, redirect

from .ui_controller import render_dashboard
from ..auth.auth import (requires_auth, get_profile_db_id, AuthErrorMode,
                         set_profile_team
                         )
from ..constants import (POST_TEAM_PERMISSION, DELETE_TEAM_PERMISSION,
                         PATCH_TEAM_PERMISSION, GET_TEAM_PERMISSION,
                         RESULT_CREATED_COUNT, DASHBOARD_URL, )
from ..forms import NewTeamForm
from ..models import M_NAME, M_TEAM_ID, M_ID
from ..services import (get_all_teams, get_team_by_id as get_team_by_id_svc,
                        create_team as create_team_svc, delete_team_by_id,
                        update_team as update_team_svc, team_exists,
                        update_user
                        )
from ..util import success_result
from ..util.exception import AbortError


@requires_auth(GET_TEAM_PERMISSION, mode=AuthErrorMode.EXCEPTION)
def all_teams(payload: dict):
    """
    Get all teams.
    :param payload: JWT payload
    :return:
    """
    teams = get_all_teams()

    return success_result(
        teams=teams
    )


@requires_auth(GET_TEAM_PERMISSION, mode=AuthErrorMode.EXCEPTION)
def get_team_by_id(payload: dict, team_id: int):
    """
    Get a team.
    :param payload: JWT payload
    :param team_id: id of team to get
    :return:
    """
    team = get_team_by_id_svc(team_id)
    if team is None:
        abort(HTTPStatus.NOT_FOUND)

    return success_result(
        team=team
    )


@requires_auth(POST_TEAM_PERMISSION, mode=AuthErrorMode.EXCEPTION)
def create_team(payload: dict):
    """
    Create a team.
    :param payload: JWT payload
    :return:
    """
    if not request.json:
        raise AbortError(HTTPStatus.BAD_REQUEST,
                         "Malformed request, expecting JSON.")

    created = create_team_svc(request.get_json())

    return make_response(
        success_result(**created), HTTPStatus.CREATED)


@requires_auth(DELETE_TEAM_PERMISSION, mode=AuthErrorMode.EXCEPTION)
def delete_team(payload: dict, team_id: int):
    """
    Delete a team.
    :param payload: JWT payload
    :param team_id: id of team to delete
    :return:
    """
    if not team_exists(team_id):
        abort(HTTPStatus.NOT_FOUND)
    deleted = delete_team_by_id(team_id)

    return make_response(
        success_result(**deleted), HTTPStatus.OK)


@requires_auth(PATCH_TEAM_PERMISSION, mode=AuthErrorMode.EXCEPTION)
def update_team(payload: dict, team_id: int):
    """
    Update a team.
    :param payload: JWT payload
    :param team_id: id of team to update
    :return:
    """
    if not team_exists(team_id):
        abort(HTTPStatus.NOT_FOUND)
    if not request.json:
        raise AbortError(HTTPStatus.BAD_REQUEST,
                         "Malformed request, expecting JSON.")

    updated = update_team_svc(team_id, request.get_json())

    return make_response(
        success_result(**updated), HTTPStatus.OK)


@requires_auth(POST_TEAM_PERMISSION)
def setup_team_ui(payload: dict):
    """
    Create a team.
    :param payload: JWT payload
    :return:
    """
    form = NewTeamForm()
    response = None

    if form.validate_on_submit():

        # Add the team to the database.
        created = create_team_svc({
            M_NAME: form.name.data
        })

        if created[RESULT_CREATED_COUNT] == 1:
            location = DASHBOARD_URL

            # Update user with new team setting.
            updated = update_user(get_profile_db_id(), {
                M_TEAM_ID: created[M_ID]
            })
            # Update profile with new team info
            set_profile_team({M_ID: created[M_ID]})

            response = redirect(location)

    if response is None:
        response = render_dashboard(new_team=True, form=form)

    return response
