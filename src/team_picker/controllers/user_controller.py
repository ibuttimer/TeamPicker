from http import HTTPStatus

from flask import abort, request, make_response
from werkzeug.utils import redirect

from .ui_controller import render_dashboard
from ..auth import (add_user_role, get_role_permissions, get_profile_auth0_id,
                    set_profile_db_id, set_profile_team,
                    set_profile_role_permissions, set_profile_role,
                    set_profile_value, set_profile_name,
                    requires_auth, Conjunction, AuthErrorMode
                    )

from ..constants import (POST_USER_PERMISSION, DELETE_USER_PERMISSION,
                         PATCH_USER_PERMISSION, GET_USER_PERMISSION,
                         DELETE_OWN_USER_PERMISSION, PATCH_OWN_USER_PERMISSION,
                         DASHBOARD_URL,
                         UNASSIGNED_TEAM_NAME, DB_ID, MANAGER_ROLE,
                         NEW_TEAM_QUERY, ROLE_PERMISSIONS, PLAYER_ROLE,
                         SET_TEAM_QUERY, RESULT_UPDATED_COUNT, YES_ARG,
                         RESULT_ONE_USER
                         )
from ..forms import RoleForm, set_role_form_choices_validators, SetTeamForm, \
    set_team_form_choices_validators
from ..models import (M_ID, M_NAME, M_SURNAME, M_ROLE, M_ROLE_ID, M_AUTH0_ID,
                      M_TEAM_ID, M_TEAM
                      )
from ..services import (get_all_users, get_user_by_id as get_user_by_id_svc,
                        create_user as create_user_svc, delete_user_by_id,
                        update_user as update_user_svc, user_exists,
                        get_team_by_name, get_team_name
                        )
from ..util import success_result
from ..util.exception import AbortError


@requires_auth(GET_USER_PERMISSION, mode=AuthErrorMode.EXCEPTION)
def all_users(payload: dict):
    """
    Get all roles.
    :param payload: JWT payload
    :return:
    """
    users = get_all_users()

    return success_result(
        users=users
    )


@requires_auth(GET_USER_PERMISSION, mode=AuthErrorMode.EXCEPTION)
def get_user_by_id(payload: dict, user_id: int):
    """
    Get a user.
    :param payload: JWT payload
    :param user_id: id of user to get
    :return:
    """
    user = get_user_by_id_svc(user_id)
    if user is None:
        abort(HTTPStatus.NOT_FOUND)

    return success_result(
        user=user
    )


@requires_auth(POST_USER_PERMISSION, mode=AuthErrorMode.EXCEPTION)
def create_user(payload: dict):
    """
    Create a user.
    :param payload: JWT payload
    :return:
    """
    if not request.json:
        raise AbortError(HTTPStatus.BAD_REQUEST,
                         "Malformed request, expecting JSON.")

    created = create_user_svc(request.get_json())

    return make_response(
        success_result(**created), HTTPStatus.CREATED)


@requires_auth()
def setup_user(payload: dict):
    """
    Setup a user.
    :param payload: JWT payload
    :return:
    """
    form = set_role_form_choices_validators(RoleForm())

    if form.validate_on_submit():
        auth0_id = get_profile_auth0_id()

        new_user = {
            M_NAME: form.name.data,
            M_SURNAME: form.surname.data,
            M_ROLE_ID: form.role_id.data,
            M_TEAM_ID: get_team_by_name(UNASSIGNED_TEAM_NAME)[M_ID],
            M_AUTH0_ID: auth0_id
        }

        # Add the user to the database.
        created = create_user_svc(new_user)
        if created is not None:
            set_profile_db_id(created[M_ID])
            user = created[RESULT_ONE_USER]
            set_profile_team({M_ID: user[M_TEAM_ID]})
            set_profile_name({
                M_NAME: user[M_NAME],
                M_SURNAME: user[M_SURNAME]
            })

        # Assign selected role in Auth0.
        result = add_user_role(form.role_id.data, auth0_id)

        set_profile_role({M_ID: form.role_id.data})
        # NOTE: after assigning a role the JWT should be refreshed to get the
        # updated permissions, but refresh tokens aren't supported by the Auth0
        # free tier as far as I can tell.
        # So, get the permissions associated with the role of the new user.
        set_profile_role_permissions(get_role_permissions(form.role_id.data))

        if result[M_ROLE] == MANAGER_ROLE:
            # Setup new team for manager.
            response = redirect(f'{DASHBOARD_URL}?{NEW_TEAM_QUERY}={YES_ARG}')
        elif result[M_ROLE] == PLAYER_ROLE:
            # Setup new team for player.
            response = redirect(f'{DASHBOARD_URL}?{SET_TEAM_QUERY}={YES_ARG}')
        else:
            # Setup complete.
            response = redirect(DASHBOARD_URL)
    else:
        # Complete user setup.
        response = make_response(
            render_dashboard(new_user=True, form=form)
        )

    return response


@requires_auth(
    permissions=[DELETE_USER_PERMISSION, DELETE_OWN_USER_PERMISSION],
    join=Conjunction.OR,
    mode=AuthErrorMode.EXCEPTION
)
def delete_user(payload: dict, user_id: int):
    """
    Delete a user.
    :param payload: JWT payload
    :param user_id: id of user to delete
    :return:
    """
    # TODO check user_id matches request in DELETE_OWN_USER_PERMISSION case
    if not user_exists(user_id):
        abort(HTTPStatus.NOT_FOUND)
    deleted = delete_user_by_id(user_id)

    return make_response(
        success_result(**deleted), HTTPStatus.OK)


@requires_auth(
    permissions=[PATCH_USER_PERMISSION, PATCH_OWN_USER_PERMISSION],
    join=Conjunction.OR,
    mode=AuthErrorMode.EXCEPTION
)
def update_user(payload: dict, user_id: int):
    """
    Update a user.
    :param payload: JWT payload
    :param user_id: id of user to delete
    :return:
    """
    if not user_exists(user_id):
        abort(HTTPStatus.NOT_FOUND)
    if not request.json:
        raise AbortError(HTTPStatus.BAD_REQUEST,
                         "Malformed request, expecting JSON.")

    updated = update_user_svc(user_id, request.get_json())

    return make_response(
        success_result(**updated), HTTPStatus.OK)


@requires_auth(
    permissions=[PATCH_USER_PERMISSION, PATCH_OWN_USER_PERMISSION],
    join=Conjunction.OR,
    mode=AuthErrorMode.EXCEPTION
)
def set_user_team(payload: dict, user_id: int):
    """
    Update a user's team.
    :param payload: JWT payload
    :param user_id: id of user to delete
    :return:
    """
    # TODO check user_id matches request in PATCH_OWN_USER_PERMISSION case
    if not user_exists(user_id):
        abort(HTTPStatus.NOT_FOUND)

    form = set_team_form_choices_validators(SetTeamForm())
    response = None

    if form.validate_on_submit():

        updated = update_user_svc(user_id, {
            M_TEAM_ID: form.team_id.data
        })

        if updated[RESULT_UPDATED_COUNT] > 0:
            set_profile_value(M_TEAM, get_team_name(form.team_id.data))

            response = redirect(DASHBOARD_URL)

    if response is None:
        # Complete user setup.
        response = make_response(
            render_dashboard(set_team=True, form=form)
        )

    return response
