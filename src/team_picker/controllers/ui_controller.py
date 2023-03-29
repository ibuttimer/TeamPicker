from http import HTTPStatus

from flask import render_template, request, url_for, flash, current_app as app
from markupsafe import Markup
from werkzeug.exceptions import abort

from .match_controller_ui import choose_by_home_id, pick_by_home_id
from ..auth.auth import (requires_auth, get_profile_db_id,
                         get_jwt_payload, get_jwt_payload_updated_at,
                         token_login_handling, check_setup_complete
                         )
from ..constants import (NEW_USER_QUERY,
                         NEW_TEAM_QUERY, SET_TEAM_QUERY, YES_ARG, NO_ARG,
                         APP_DATETIME_FMT, ACCESS_TOKEN
                         )
from ..forms import (RoleForm, set_role_form_choices_validators, NewTeamForm,
                     SetTeamForm, set_team_form_choices_validators
                     )
from ..models import M_HOME_ID, M_AWAY_ID
from ..services import get_selected_and_unconfirmed, get_team_name
from ..util import local_datetime


def home():
    """
    Home screen.
    :return:
    """
    return render_template('home.html', title="Home")


def render_dashboard(new_user=False,
                     new_team=False,
                     set_team=False,
                     form=None):
    """
    Render dashboard screen.
    :return:
    """
    if new_user:
        if form is None:
            form = set_role_form_choices_validators(RoleForm())
        # Create user in database, on submit.
        submit_action = url_for('setup_user')
        submit_text = "Create"
    elif new_team:
        if form is None:
            form = NewTeamForm()
        # Create manager's team in database, on submit.
        submit_action = url_for('setup_team_ui')
        submit_text = "Create"
    elif set_team:
        if form is None:
            form = set_team_form_choices_validators(SetTeamForm())
        # Set player's team in database, on submit.
        submit_action = url_for('set_user_team', user_id=get_profile_db_id())
        submit_text = "Set"
    else:
        # Basic dashboard.
        form = None
        submit_action = None
        submit_text = None

        # Show messages for unconfirmed match selections.
        db_id = get_profile_db_id()
        for match in get_selected_and_unconfirmed(db_id):
            url = url_for('match_selections', match_id=match.id)
            opposition = get_team_name(
                pick_by_home_id(match, M_AWAY_ID, M_HOME_ID))

            flash(
                Markup(
                    render_template(
                        'messages/availability_unconfirmed.html',
                        start_time=match.start_time.strftime(APP_DATETIME_FMT),
                        venue=choose_by_home_id(match.home_id, "home", "away"),
                        opposition=opposition,
                        url=url)
                )
            )

    return render_template('dashboard.html',
                           new_user=new_user,
                           new_team=new_team,
                           set_team=set_team,
                           form=form,
                           submit_action=submit_action,
                           submit_text=submit_text,
                           userinfo_pretty=app.json.dumps(
                               get_jwt_payload()),
                           last_login=local_datetime(
                               get_jwt_payload_updated_at())
                           .strftime(APP_DATETIME_FMT),
                           title="Dashboard")


@requires_auth()
def dashboard(payload: dict):
    """
    Dashboard screen.
    :return:
    """
    query = check_setup_complete()
    if query is not None:
        new_user = (NEW_USER_QUERY == query)
        new_team = (NEW_TEAM_QUERY == query)
        set_team = (SET_TEAM_QUERY == query)
    else:
        new_user = \
            request.args.get(
                NEW_USER_QUERY, NO_ARG, type=str).lower() == YES_ARG
        new_team = \
            request.args.get(
                NEW_TEAM_QUERY, NO_ARG, type=str).lower() == YES_ARG
        set_team = \
            request.args.get(
                SET_TEAM_QUERY, NO_ARG, type=str).lower() == YES_ARG

    return render_dashboard(new_user=new_user,
                            new_team=new_team,
                            set_team=set_team)


def token_login():
    """
    Login using an access token.
    :return:
    """
    if not request.is_json:
        abort(HTTPStatus.BAD_REQUEST)

    json_body = request.get_json()
    return token_login_handling(json_body[ACCESS_TOKEN])
