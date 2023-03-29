from typing import Union, Any

from flask_wtf import FlaskForm
from wtforms import (
    SelectField, StringField, RadioField, DateTimeField, BooleanField,
    IntegerField
)
from wtforms.validators import (
    InputRequired, AnyOf, NumberRange, ValidationError, NoneOf
)

from .validators import ValidateDateTime
from ..models.exception import ModelError
from ..constants import APP_DATETIME_FMT, APP_DATE_FMT
from ..services import (get_all_roles, get_all_teams, get_unassigned_team_id,
                        verify_match, get_all_team_names
                        )
from ..models import M_ID, M_ROLE, M_NAME, M_START_TIME, M_HOME_ID, M_AWAY_ID
from ..util import (
    current_datetime, FormArgs, NO_OPTION_SELECTED, HOME_VENUE, VENUE_CHOICES,
    VENUES, DateRange, DATE_RANGE_CHOICES, DATE_RANGES
)
from ..auth import get_profile_team_id
from ..util.misc import choose_by_eq, choose_by_home_venue

TEAM_SCORE = "team_score"
OPPOSITION_SCORE = "opposition_score"


class RoleForm(FlaskForm):
    name = StringField(
        'Name', validators=[InputRequired()]
    )
    surname = StringField(
        'Surname', validators=[InputRequired()]
    )
    # Choices & validators need to be set dynamically in controller.
    role_id = SelectField(
        'Role', validators=[], choices=[], coerce=int
    )


def set_role_form_choices_validators(form: RoleForm) -> RoleForm:
    """
    Set the choices and validators for a RoleForm
    :param form: form to configure
    :return:
    """
    all_roles = get_all_roles()
    roles = [(r[M_ID], r[M_ROLE]) for r in all_roles]
    roles.insert(0, (NO_OPTION_SELECTED, 'Select role'))
    role_options = [r[M_ID] for r in all_roles]

    form.role_id.choices = roles
    form.role_id.validators = [
        AnyOf(role_options, message="Please select a role from the list")
    ]

    return form


def validate_team(form, field):
    if field.data in get_all_team_names():
        raise ValidationError(f'A team with the selected name already exists.')


class NewTeamForm(FlaskForm):
    name = StringField(
        'Name', validators=[InputRequired(),
                            validate_team
                            ]
    )


class SetTeamForm(FlaskForm):
    # Choices & validators need to be set dynamically in controller.
    team_id = SelectField(
        'Team id', validators=[], choices=[], coerce=int
    )


def _team_choices_validators(exclude: Union[int, list[int]]) -> (list, list):
    """
    Set the choices and validators for a SetTeamForm
    :param exclude: id(s) of team(s) to exclude
    :return: tuple of choices, and valid options
    """
    all_teams = get_all_teams()
    if isinstance(exclude, list):
        all_teams = [t for t in all_teams if t[M_ID] not in exclude]
    elif isinstance(exclude, int):
        all_teams = [t for t in all_teams if t[M_ID] != exclude]
    teams = [(t[M_ID], t[M_NAME]) for t in all_teams]
    teams.insert(0, (NO_OPTION_SELECTED, 'Select team'))
    team_options = [t[M_ID] for t in all_teams]

    return teams, team_options


def set_team_form_choices_validators(form: SetTeamForm) -> SetTeamForm:
    """
    Set the choices and validators for a SetTeamForm
    :param form: form to configure
    :return:
    """
    teams, team_options = _team_choices_validators(
        get_unassigned_team_id())

    form.team_id.choices = teams
    form.team_id.validators = [
        AnyOf(team_options, message="Please select a team from the list")
    ]

    return form


def validate_match(form, field):
    try:
        verify_match({
            M_START_TIME: form.start_time.data,
            M_HOME_ID: choose_by_home_venue(
                form.venue.data, get_profile_team_id(), form.opposition.data),
            M_AWAY_ID: choose_by_home_venue(
                form.venue.data, form.opposition.data, get_profile_team_id())
        })
    except ModelError as me:
        raise ValidationError(me.error)


class MatchForm(FlaskForm):
    venue = RadioField(
        'Venue', validators=[
            InputRequired(),
            AnyOf(VENUES, message="Please select a venue")
        ],
        choices=VENUE_CHOICES, coerce=int, default=HOME_VENUE
    )
    # Choices & validators need to be set dynamically in controller.
    opposition = SelectField(
        'Opposition', validators=[], choices=[], coerce=int
    )
    # Default configuration is future date/times only.
    start_time = DateTimeField(
        'Start time',
        validators=[InputRequired(),
                    ValidateDateTime(
                        min_dt=ValidateDateTime.FIELD_DEFAULT,
                        dt_format=APP_DATETIME_FMT),
                    validate_match
                    ],
        format=APP_DATETIME_FMT,
        default=current_datetime()
    )
    result = BooleanField(
        'Result',
        default=False
    )
    team_score = IntegerField(
        'Team score',
        validators=[InputRequired(),
                    NumberRange(min=0, message="Score may not be negative")
                    ],
        default=0
    )
    opposition_score = IntegerField(
        'Opposition score',
        validators=[InputRequired(),
                    NumberRange(min=0, message="Score may not be negative")
                    ],
        default=0
    )


class MatchSearchForm(FlaskForm):
    # Choices & validators need to be set dynamically in controller.
    opposition = SelectField(
        'Opposition', validators=[], choices=[], coerce=int
    )
    date_range = RadioField(
        'Date range', validators=[
            InputRequired(),
            AnyOf(DATE_RANGES, message="Please select a date range")
        ],
        choices=DATE_RANGE_CHOICES, coerce=DateRange.coerce,
        default=DateRange.IGNORE_DATE
    )
    start_time = DateTimeField(
        'Start time',
        validators=[InputRequired(),
                    ValidateDateTime(dt_format=APP_DATE_FMT)
                    ],
        format=APP_DATE_FMT,
        default=current_datetime()
    )


def set_match_form_choices_validators(
        form: Union[MatchForm, MatchSearchForm], team_id: int,
        *args) -> MatchForm:
    """
    Set the choices and validators in a MatchForm.
    :param form: form to configure
    :param team_id: id of team setting up the match
    :return:
    """
    teams, team_options = _team_choices_validators(
        [get_unassigned_team_id(), team_id])

    form.opposition.choices = teams
    form.opposition.validators = [
        AnyOf(team_options, message="Please select a team from the list"),
        NoneOf([team_id], message="Duplicate home and away team")
    ] if FormArgs.TEAM_REQ in args or FormArgs.TEAM_NOT_REQ not in args \
        else []

    if FormArgs.FREE_MIN in args:
        form.start_time.validators = [
            InputRequired(),
            ValidateDateTime(dt_format=APP_DATETIME_FMT)
        ]

    return form
