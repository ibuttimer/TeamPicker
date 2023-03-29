from enum import IntEnum, auto
from http import HTTPStatus
from typing import Optional, Any, Union

from flask import (abort, request, make_response, url_for,
                   render_template, redirect, Response
                   )
from werkzeug.datastructures import MultiDict

from .match_controller_api import delete_match_impl
from ..auth import get_profile_team_id
from ..auth.auth import (
    requires_auth, Conjunction, check_auth, get_profile_db_id,
    get_profile_is_manager
)
from ..constants import (POST_MATCH_PERMISSION, DELETE_MATCH_PERMISSION,
                         PATCH_MATCH_PERMISSION, GET_MATCH_PERMISSION,
                         NEW_QUERY, UPDATE_QUERY,
                         DASHBOARD_URL, ORDER_QUERY, GET, RESULT_UPDATED_COUNT,
                         APP_DATETIME_FMT, SEARCH_QUERY,
                         OPPOSITION, DATE_RANGE, ORDER_DATE_DESC, APP_DATE_FMT,
                         SELECTIONS_QUERY, PLAYER_ROLE, POST, YES_ARG, NO_ARG,
                         PATCH_OWN_MATCH_PERMISSION, TEAM, VENUE, PATCH
                         )
from ..forms import (MatchForm, set_match_form_choices_validators
                     )
from ..forms.forms import MatchSearchForm, TEAM_SCORE, OPPOSITION_SCORE
from ..forms.misc import (NO_OPTION_SELECTED, HOME_VENUE, AWAY_VENUE, DateRange,
                          DATE_RANGE_CHOICES
                          )
from ..models import (M_START_TIME, M_HOME_ID, M_AWAY_ID, Match, M_ID,
                      M_SCORE_HOME, M_SCORE_AWAY, M_RESULT, M_NAME, M_SURNAME,
                      M_SELECTIONS, entity_to_dict
                      )
from ..models.exception import ModelError
from ..services import (get_all_matches, get_match_by_id as get_match_by_id_svc,
                        create_match as create_match_svc,
                        update_match as update_match_svc, get_team_name,
                        get_users_by_role_and_team,
                        get_role_by_role, set_selection,
                        is_selected_and_confirmed, SelectChoice,
                        set_confirmation, get_match_by_id_and_team, is_selected
                        )
from ..util import FormArgs, VENUE_CHOICES
from ..util.exception import AbortError
from ..util.misc import choose_by_ls_eq_gr, choose_by_home_venue, choose_by_eq

POST_PATCH_PERMISSION = [POST_MATCH_PERMISSION, PATCH_MATCH_PERMISSION]
GET_POST_PERMISSION = [GET_MATCH_PERMISSION, POST_MATCH_PERMISSION]
GET_PATCH_PERMISSION = [GET_MATCH_PERMISSION, PATCH_MATCH_PERMISSION]
GET_POST_PATCH_PERMISSION = GET_POST_PERMISSION + [PATCH_MATCH_PERMISSION]


class ReqAction(IntEnum):
    """
    Enum representing request actions.
    """
    NEW = auto()
    UPDATE = auto()
    SELECTIONS = auto()
    SEARCH = auto()
    LIST = auto()

    @staticmethod
    def from_request():
        action = ReqAction.LIST
        for query, chk_action, _ in QUERY_ACTION_ARGS:
            if request.args.get(query, NO_ARG, type=str).lower() == YES_ARG:
                action = chk_action
                break
        return action

    @staticmethod
    def action_index(action):
        action_idx = -1
        idx = 0
        for _, chk_action, _ in QUERY_ACTION_ARGS:
            if action == chk_action:
                action_idx = idx
                break
            else:
                idx = idx + 1
        return action_idx


QUERY_ACTION_ARGS = [
    # query, action, args
    (NEW_QUERY, ReqAction.NEW,
     # base url, title, heading, submit_text
     ('create_match_ui', 'New match', 'New match', 'Create')),  # new
    (UPDATE_QUERY, ReqAction.UPDATE,
     ('match_by_id_ui', 'Update match', 'Update match', 'Update')),  # update
    (SELECTIONS_QUERY, ReqAction.SELECTIONS,
     ('match_selections',
      'Match selections', 'Match selections', 'Update')),  # selections
    (SEARCH_QUERY, ReqAction.SEARCH,
     ('search_match_ui', 'Search match', 'Search match', 'Search'))  # search
]
QUERY_IDX = 0
REQ_ACTION_IDX = 1
ARGS_IDX = 2


def render_matches(action: ReqAction = ReqAction.LIST,
                   form=None,
                   match_list=None,
                   match=None,
                   player_list=None,
                   criteria=None,
                   submit_action=None,
                   title=None,
                   heading=None,
                   submit_text=None):
    """
    Render the matches page.
    :param action:
    :param form:
    :param match_list:
    :param match:
    :param player_list:
    :param criteria:
    :param submit_action:
    :param title:
    :param heading:
    :param submit_text:
    :return:
    """
    return render_template('matches.html',
                           match_new=(action == ReqAction.NEW),
                           match_update=(action == ReqAction.UPDATE),
                           match_selections=(action == ReqAction.SELECTIONS),
                           match_search=(action == ReqAction.SEARCH),
                           form=form,
                           match_list=match_list,
                           match=match,
                           player_list=player_list,
                           criteria=criteria,
                           submit_action=submit_action,
                           cancel_url=url_for('dashboard'),
                           title=title,
                           heading=heading,
                           submit_text=submit_text)


def pick_by_home_id(match: dict, home_key: str, away_key: str):
    """
    Pick value from match based on home team.
    :param match:   match to pick value from
    :param home_key:  key for home value
    :param away_key:  key for away value
    :return: 
    """
    match = entity_to_dict(match)
    return match[
        choose_by_home_id(match, home_key, away_key)
    ]


def matches_for_ui(order: str = None, criteria: dict = None):
    """
    Get matches and format for UI.
    :param order:       order results by
    :param criteria:    filter criteria
    :return: list of all matches.
    """
    return [{
        M_ID: match[M_ID],
        M_START_TIME: match[M_START_TIME].strftime(APP_DATETIME_FMT),
        VENUE: choose_by_home_id(match, "Home", "Away"),
        OPPOSITION: get_team_name(
            pick_by_home_id(match, M_AWAY_ID, M_HOME_ID)),
        "result": choose_by_ls_eq_gr(
            # Test value is opposition team score.
            pick_by_home_id(match, M_SCORE_AWAY, M_SCORE_HOME),
            # Expected is manager's team score.
            pick_by_home_id(match, M_SCORE_HOME, M_SCORE_AWAY),
            "fas fa-chevron-down",  # Less than is loss.
            "fas fa-equals",  # Equal is draw.
            "fas fa-chevron-up"  # Greater than is win
        ) if match[M_RESULT] else "fas fa-question-circle",
        "result_tip": choose_by_ls_eq_gr(
            # Test value is opposition team score.
            pick_by_home_id(match, M_SCORE_AWAY, M_SCORE_HOME),
            # Expected is manager's team score.
            pick_by_home_id(match, M_SCORE_HOME, M_SCORE_AWAY),
            "Loss",
            "Draw",
            "Win"
        ) if match[M_RESULT] else "Result not final",
        "score_tip": f"{get_team_name(match[M_HOME_ID])} {match[M_SCORE_HOME]}"
                     f" - "
                     f"{get_team_name(match[M_AWAY_ID])} {match[M_SCORE_AWAY]}",
        "score": f"{match[M_SCORE_HOME]} - {match[M_SCORE_AWAY]}"
                 if match[M_RESULT] else ""
    } for match in get_all_matches(order_by=order, criteria=criteria)]


def matches_render_args(action: ReqAction = ReqAction.LIST, match_id: int = 0):
    if action != ReqAction.LIST:
        index = ReqAction.action_index(action)
        url, title, heading, submit_text = QUERY_ACTION_ARGS[index][ARGS_IDX]
        submit_action = url_for(url, match_id=match_id) \
            if action == ReqAction.UPDATE or action == ReqAction.SELECTIONS \
            else url_for(url)
    else:
        submit_action = None
        title = 'Matches'
        heading = None
        submit_text = None

    return {
        "submit_action": submit_action,
        "title": title,
        "heading": heading,
        "submit_text": submit_text
    }


def search_criteria_description(criteria: dict) -> Optional[str]:
    """
    Generate a search criteria description.
    :param criteria: criteria to describe
    :return:
    """
    if criteria is not None:
        opposition_criteria = None
        if OPPOSITION in criteria.keys():
            opposition = criteria[OPPOSITION]
            if opposition != NO_OPTION_SELECTED:
                opposition_criteria = f"Opposition: '{get_team_name(opposition)}'"

        date_criteria = None
        if DATE_RANGE in criteria.keys() and M_START_TIME in criteria.keys():
            date_range = criteria[DATE_RANGE]
            if date_range != DateRange.IGNORE_DATE:
                index = [c[0] for c in DATE_RANGE_CHOICES].index(date_range)
                date_criteria = \
                    f"{DATE_RANGE_CHOICES[index][1]}: " \
                    f"'{criteria[M_START_TIME].strftime(APP_DATE_FMT)}'"

        if opposition_criteria is not None and date_criteria is not None:
            criteria = f"{opposition_criteria} and {date_criteria}"
        elif opposition_criteria is not None:
            criteria = opposition_criteria
        elif date_criteria is not None:
            criteria = date_criteria
        else:
            criteria = None

        return criteria


@requires_auth(permissions=GET_POST_PERMISSION, join=Conjunction.OR)
def matches_ui(payload: dict):
    """
    Matches screen.
    :param payload: JWT payload
    :return:
    """
    action = ReqAction.from_request()
    order = request.args.get(ORDER_QUERY, NO_ARG, type=str).lower()

    if action == ReqAction.UPDATE:
        raise AbortError(HTTPStatus.BAD_REQUEST,
                         "Malformed request, unrecognised query parameter.")

    if action == ReqAction.NEW:
        # Need post for new.
        auth_result = check_auth(permission=POST_MATCH_PERMISSION)
        if isinstance(auth_result, Response):
            # Failed auth check, return redirect response.
            return auth_result

    if action != ReqAction.LIST:
        form = set_match_form_choices_validators(
            MatchSearchForm() if action == ReqAction.SEARCH else MatchForm(),
            get_profile_team_id())
        match_list = None
    else:
        # Get list of matches
        form = None
        match_list = matches_for_ui(order=order, criteria={
            TEAM: get_profile_team_id()
        })

    return render_matches(action=action,
                          form=form,
                          match_list=match_list,
                          **matches_render_args(action)
                          )


def data_from_form(form: MatchForm, profile_team_id: int) -> dict:
    """
    Retrieve match data from a match form. For user convenience purposes, the
    form uses 'team_score' & 'opposition_score' but the database uses
    'score_home' and 'score_away'.
    :param form: match form
    :param profile_team_id: team id of manager
    :return:
    """
    return {
        M_HOME_ID: choose_by_home_venue(
            form.venue.data, profile_team_id, form.opposition.data),
        M_AWAY_ID: choose_by_home_venue(
            form.venue.data, form.opposition.data, profile_team_id),
        M_START_TIME: form.start_time.data,
        M_RESULT: form.result.data,
        M_SCORE_HOME: choose_by_home_venue(
            form.venue.data, form.team_score.data, form.opposition_score.data),
        M_SCORE_AWAY: choose_by_home_venue(
            form.venue.data, form.opposition_score.data, form.team_score.data)
    }


def data_to_form(match: dict) -> dict:
    """
    Generate match data for a match form. For user convenience purposes, the
    form uses 'team_score' & 'opposition_score' but the database uses
    'score_home' and 'score_away'.
    :param match: match data
    :return:
    """
    return {
        VENUE: choose_by_home_id(match, HOME_VENUE, AWAY_VENUE),
        OPPOSITION: pick_by_home_id(match, M_AWAY_ID, M_HOME_ID),
        M_START_TIME: match[M_START_TIME].strftime(APP_DATETIME_FMT),
        M_RESULT: match[M_RESULT],
        TEAM_SCORE: pick_by_home_id(match, M_SCORE_HOME, M_SCORE_AWAY),
        OPPOSITION_SCORE: pick_by_home_id(match, M_SCORE_AWAY, M_SCORE_HOME)
    }


@requires_auth(permission=POST_MATCH_PERMISSION)
def create_match_ui(payload: dict):
    """
    Create a match.
    :param payload: JWT payload
    :return:
    """
    profile_team_id = get_profile_team_id()
    response = None
    form = set_match_form_choices_validators(MatchForm(), profile_team_id)

    if form.validate_on_submit():

        new_match = Match.empty_entity(
            data_from_form(form, profile_team_id)
        )

        # Add the match to the database.
        try:
            created = create_match_svc(new_match)

            response = make_response(
                redirect(DASHBOARD_URL)
            )
        except ModelError as me:
            start_time_errors = form.errors[form.start_time.name] \
                if form.start_time.name in form.errors.keys() else []

            start_time_errors.append(me.error)
            form.errors[form.start_time.name] = start_time_errors

    if response is None:
        # Complete match setup.
        response = make_response(
            render_matches(action=ReqAction.NEW,
                           form=form,
                           **matches_render_args(ReqAction.NEW)
                           )
        )

    return response


def get_team_id_and_match(match_id: int):
    """
    Get user's team id and match.
    :param match_id: id of match to get
    :return: tuple of team id and match
    :raise  HTTPException if match does not exist or current user's team not
            involved.
    """
    profile_team_id = get_profile_team_id()
    match = get_match_by_id_and_team(match_id, profile_team_id)
    if match is None:
        # None existent match or not user's team match.
        abort(HTTPStatus.NOT_FOUND)
    return profile_team_id, match


@requires_auth(permissions=GET_POST_PATCH_PERMISSION, join=Conjunction.OR)
def match_by_id_ui(payload: dict, match_id: int):
    """
    Match get/update.
    :param payload: JWT payload
    :param match_id: id of match to update
    :return:

    A GET returns the form to be edited
    A PATCH/POST persists the updates
    """
    profile_team_id, match = get_team_id_and_match(match_id)

    is_get = (request.method == GET)
    is_update = (request.method == PATCH) or (request.method == POST)
    response = None

    if is_get:
        # Match data
        form_data = data_to_form(match)
        form = MatchForm(formdata=MultiDict(form_data))
    elif is_update:
        # Need patch/post for update.
        auth_result = check_auth(permissions=POST_PATCH_PERMISSION,
                                 join=Conjunction.OR)
        if isinstance(auth_result, Response):
            # Failed auth check, return redirect response.
            return auth_result

        form = MatchForm()
    else:
        abort(HTTPStatus.BAD_REQUEST)

    # Allow past date/times for start time.
    set_match_form_choices_validators(form, profile_team_id, FormArgs.FREE_MIN)

    if is_update and form.validate_on_submit():
        # Persist updates. Updating resets the selections, not great UX but
        # that is it for now.
        updates = data_from_form(form, profile_team_id) | {M_SELECTIONS: []}
        updated = update_match_svc(match_id, updates)

        if updated[RESULT_UPDATED_COUNT] > 0:
            response = make_response(
                redirect(DASHBOARD_URL)
            )

    if response is None:
        response = make_response(
            render_matches(action=ReqAction.UPDATE,
                           form=form,
                           **matches_render_args(
                               ReqAction.UPDATE, match_id=match[M_ID]))
        )

    return response


def player_list_entry(match_id: int, player: dict):
    selected, confirmed = is_selected_and_confirmed(match_id, player[M_ID])
    return {
        M_ID: player[M_ID],
        M_NAME: f"{player[M_NAME]} {player[M_SURNAME]}",
        'is_self': (player[M_ID] == get_profile_db_id()),
        "selected": selected,
        "toggle_select_url":
            url_for('match_user_selection',
                    match_id=match_id, user_id=player[M_ID]),
        "confirmed": confirmed,
        "confirm_select_url":
            url_for('match_user_confirm',
                    match_id=match_id, user_id=player[M_ID])
    }


@requires_auth(permission=GET_MATCH_PERMISSION)
def match_selections(payload: dict, match_id: int):
    """
    Get/update match selections.
    :param payload: JWT payload
    :param match_id: id of match to update
    :return:

    A GET returns the match selections
    A POST persists the updates
    """
    profile_team_id, match = get_team_id_and_match(match_id)

    # Match data
    match_info = {
        VENUE: VENUE_CHOICES[
            choose_by_home_id(match, HOME_VENUE, AWAY_VENUE)][1],
        OPPOSITION: get_team_name(
            pick_by_home_id(match, M_AWAY_ID, M_HOME_ID)),
        M_START_TIME: match[M_START_TIME].strftime(APP_DATETIME_FMT),
        M_ID: match[M_ID]
    }

    players = get_users_by_role_and_team(
        get_role_by_role(PLAYER_ROLE)[M_ID], profile_team_id)

    player_list = [
        player_list_entry(match_id, player) for player in players
    ]

    return make_response(
        render_matches(action=ReqAction.SELECTIONS,
                       match=match_info,
                       player_list=player_list,
                       **matches_render_args(
                           ReqAction.SELECTIONS, match_id=match[M_ID]))
    )


@requires_auth(permissions=POST_PATCH_PERMISSION, join=Conjunction.OR)
def match_user_selection(payload: dict, match_id: int, user_id: int):
    """
    Update match selections.
    :param payload: JWT payload
    :param match_id: id of match
    :param user_id: id of user
    :return:
    """
    profile_team_id, match = get_team_id_and_match(match_id)

    set_selection(
        match_id, user_id,
        SelectChoice.from_request(dflt_value=SelectChoice.TOGGLE))

    return redirect(
        url_for('match_selections', match_id=match_id))


@requires_auth(permission=PATCH_OWN_MATCH_PERMISSION)
def match_user_confirm(payload: dict, match_id: int, user_id: int):
    """
    Update match availability for user.
    :param payload: JWT payload
    :param match_id: id of match
    :param user_id: id of user
    :return:
    """
    profile_team_id, match = get_team_id_and_match(match_id)

    if get_profile_is_manager():
        # Managers don't play.
        abort(HTTPStatus.NOT_FOUND)

    if not is_selected(match_id, user_id):
        # User not selected.
        abort(HTTPStatus.NOT_FOUND)

    confirmed = SelectChoice.from_request(dflt_value=SelectChoice.MAYBE)

    set_confirmation(match_id, user_id, confirmed)

    return redirect(
        url_for('match_selections', match_id=match_id))


@requires_auth(DELETE_MATCH_PERMISSION)
def delete_match_ui(payload: dict, match_id: int):
    """
    Delete a match via UI endpoint.
    :param payload: JWT payload
    :param match_id: id of match to delete
    :return:
    """
    profile_team_id, match = get_team_id_and_match(match_id)

    return delete_match_impl(match_id)


@requires_auth(GET_MATCH_PERMISSION)
def search_match_ui(payload: dict):
    """
    Search for matches.
    :param payload: JWT payload
    :return:
    """
    order = request.args.get(ORDER_QUERY, NO_ARG, type=str).lower()

    profile_team_id = get_profile_team_id()
    form = set_match_form_choices_validators(
        MatchSearchForm(), profile_team_id, FormArgs.TEAM_NOT_REQ)

    if form.validate_on_submit():

        criteria = {
            OPPOSITION: form.opposition.data,
            M_START_TIME: form.start_time.data,
            DATE_RANGE: form.date_range.data,
            TEAM: profile_team_id   # User can only see their team's info.
        }

        match_list = matches_for_ui(order=order, criteria=criteria)

        response = make_response(
            render_matches(match_list=match_list,
                           title='Match search results',
                           criteria=search_criteria_description(criteria))
        )
    else:
        # Complete search.
        response = make_response(
            render_matches(action=ReqAction.SEARCH,
                           form=form,
                           **matches_render_args(ReqAction.SEARCH)
                           )
        )

    return response


def choose_by_home_id(home: Union[int, dict],
                      home_value: Any, away_value: Any):
    """
    Choose home or away value, based on home team id.
    :param home:     home team id or match dict
    :param home_value:  value representing home
    :param away_value:  value representing away
    :return:
    """
    home = entity_to_dict(home)
    return choose_by_eq(get_profile_team_id(),
                        home if isinstance(home, int) else home[M_HOME_ID],
                        home_value, away_value)


