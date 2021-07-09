from datetime import datetime
from http import HTTPStatus
from typing import Any, NewType, Union

from sqlalchemy import (Column, Integer, String, UniqueConstraint,
                        CheckConstraint
                        )

from .models_misc import *

from .db_session import db, db_session

from .exception import ModelError
from ..constants import PRE_CONFIG_ROLE_NAMES, UNASSIGNED_TEAM_NAME
from ..util import CONFIRMED_STATUS, NO_STATUS

# Database table names
TEAMS_TABLE = "teams"
ROLES_TABLE = "roles"
USERS_TABLE = "users"
MATCHES_TABLE = "matches"
SELECTIONS_TABLE = "selections"

# Database column names.
M_ID = "id"
M_ROLE = "role"
M_NAME = "name"
M_SURNAME = "surname"
M_AUTH0_ID = "auth0_id"
M_ROLE_ID = "role_id"
M_TEAM_ID = "team_id"
M_TEAM = "team"

M_HOME_ID = "home_id"
M_AWAY_ID = "away_id"
M_START_TIME = "start_time"
M_RESULT = "result"
M_SCORE_HOME = "score_home"
M_SCORE_AWAY = "score_away"
M_SELECTIONS = "selections"

M_MATCH_ID = 'match_id'
M_USER_ID = 'user_id'
M_CONFIRMED = 'confirmed'


def _check_correct_type(obj: Any, name: str, obj_type: Any):
    """
    Check object is the correct type
    :param obj:      object to check
    :param name:     name of object
    :param obj_type: type of object
    """
    if obj is None:
        raise ModelError(HTTPStatus.UNPROCESSABLE_ENTITY,
                         f"Missing required value: {name}")
    elif not isinstance(obj, obj_type):
        raise ModelError(HTTPStatus.UNPROCESSABLE_ENTITY,
                         f"Invalid {name} value: expected '{obj_type}' "
                         f"but got '{type(obj)}'")


# many-to-many relationship between matches and users
MatchSelections = db.Table(SELECTIONS_TABLE, db.Model.metadata,
                           db.Column(M_MATCH_ID, db.Integer,
                                     db.ForeignKey(f"{MATCHES_TABLE}.id"),
                                     primary_key=True),
                           db.Column(M_USER_ID, db.Integer,
                                     db.ForeignKey(f"{USERS_TABLE}.id"),
                                     primary_key=True),
                           db.Column(M_CONFIRMED, db.Integer,
                                     CheckConstraint(
                                         f'{M_CONFIRMED}<={CONFIRMED_STATUS}'),
                                     nullable=False, default=NO_STATUS)
                           )


class Role(MultiDictMixin, db.Model):
    __tablename__ = ROLES_TABLE

    # Auto-incrementing, unique primary key
    id = Column(Integer, primary_key=True)
    # Role
    role = Column(String(80), nullable=False)

    def __init__(self, role: str = None):
        self.role = role

    def __repr__(self):
        return f"<Role(id={self.id}, role={self.role})>"


class User(MultiDictMixin, db.Model):
    __tablename__ = USERS_TABLE

    # Auto-incrementing, unique primary key
    id = Column(Integer, primary_key=True)
    # First name
    name = Column(String(80), nullable=False)
    # Surname
    surname = Column(String(80), nullable=False)
    # Auth0 user ID
    auth0_id = Column(String(80), nullable=False, unique=True)
    # Role
    role_id = db.Column(db.Integer, db.ForeignKey(f"{ROLES_TABLE}.id"),
                        nullable=False)
    role = db.relationship('Role')
    # Team
    team_id = db.Column(db.Integer, db.ForeignKey(f"{TEAMS_TABLE}.id"),
                        nullable=True, default=0)
    team = db.relationship('Team')

    def __init__(self, name: str = None, surname: str = None,
                 auth0_id: str = None, role_id: int = None,
                 team_id: int = None):
        self.name = name
        self.surname = surname
        self.auth0_id = auth0_id
        self.role_id = role_id
        self.team_id = team_id

    @staticmethod
    def is_valid_entity(entity: dict, attribs: list = None) -> dict:
        """
        Validate and sanitise a user dict
        :param entity:      entity to check
        :param attribs:     attributes to check
        :return: Sanitised dict
        """
        if attribs is None:
            attribs = [M_NAME, M_SURNAME, M_AUTH0_ID, M_ROLE_ID, M_TEAM_ID]

        # Check all data is valid
        _check_correct_type(entity, 'user', dict)
        valid_entity = {}
        for name, obj_type in [(M_NAME, str), (M_SURNAME, str),
                               (M_AUTH0_ID, str),
                               (M_ROLE_ID, int), (M_TEAM_ID, int)]:
            if name in attribs:
                obj = entity[name] if name in entity.keys() else None
                _check_correct_type(obj, name, obj_type)

                if obj_type == str:
                    obj = obj.strip()
                    if len(obj) == 0:
                        raise ModelError(HTTPStatus.UNPROCESSABLE_ENTITY,
                                         f"Empty {name} value")
                elif obj_type == int:
                    if obj < 1:
                        raise ModelError(HTTPStatus.UNPROCESSABLE_ENTITY,
                                         f"Invalid {name} value")

                valid_entity[name] = obj

        return valid_entity

    @staticmethod
    def from_dict(entity: dict):
        """
        Create a User model from a dict.
        :param entity: dict to create from
        :return: new model
        """
        valid_user = User.is_valid_entity(entity)

        user = User(**valid_user)

        return user

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, " \
               f"surname={self.surname}, auth0_id={self.auth0_id}, " \
               f"role_id={self.role_id}, " \
               f"team_id={self.team_id})>"


class Team(MultiDictMixin, db.Model):
    __tablename__ = TEAMS_TABLE

    # Auto-incrementing, unique primary key
    id = Column(Integer, primary_key=True)
    # Team name
    name = Column(String(80), unique=True, nullable=False)

    def __init__(self, name: str = None):
        self.name = name

    @staticmethod
    def is_valid_entity(entity: dict, attribs: list = None) -> dict:
        """
        Validate and sanitise a team dict
        :param entity:      entity to check
        :param attribs:     attributes to check
        :return: Sanitised dict
        """
        if attribs is None:
            attribs = [M_NAME]

        # Check all data is valid
        _check_correct_type(entity, 'team', dict)
        valid_entity = {}
        for name, obj_type in [(M_NAME, str)]:
            if name in attribs:
                obj = entity[name] if name in entity.keys() else None
                _check_correct_type(obj, name, obj_type)

                if obj_type == str:
                    obj = obj.strip()
                    if len(obj) == 0:
                        raise ModelError(HTTPStatus.UNPROCESSABLE_ENTITY,
                                         f"Empty {name} value")

                valid_entity[name] = obj

        return valid_entity

    @staticmethod
    def from_dict(entity: dict):
        """
        Create a Team model from a dict.
        :param entity: dict to create from
        :return: new model
        """
        valid_team = Team.is_valid_entity(entity)

        team = Team(name=valid_team[M_NAME])

        return team

    def __repr__(self):
        return f"<Team(id={self.id}, name={self.name})>"


MATCH_VARS_AND_TYPES = [(M_HOME_ID, int), (M_AWAY_ID, int),
                        (M_START_TIME, datetime), (M_RESULT, bool),
                        (M_SCORE_HOME, int), (M_SCORE_AWAY, int),
                        (M_SELECTIONS, list)]


class Match(MultiDictMixin, db.Model):
    __tablename__ = MATCHES_TABLE

    # Auto-incrementing, unique primary key
    id = Column(Integer, primary_key=True)
    # Home team
    home_id = db.Column(db.Integer, db.ForeignKey(f"{TEAMS_TABLE}.id"),
                        nullable=False)
    home = db.relationship('Team', foreign_keys=[home_id])
    # Away team
    away_id = db.Column(db.Integer, db.ForeignKey(f"{TEAMS_TABLE}.id"),
                        nullable=False)
    away = db.relationship('Team', foreign_keys=[away_id])
    # Start time
    start_time = db.Column(db.DateTime, nullable=False)
    # Result
    result = db.Column(db.Boolean, nullable=False, default=False)
    # Score for home team
    score_home = db.Column(db.Integer, CheckConstraint('score_home>=0'),
                           nullable=False, default=0)
    # Score for away team
    score_away = db.Column(db.Integer, CheckConstraint('score_away>=0'),
                           nullable=False, default=0)
    # Users selected for match
    selections = db.relationship('User', secondary=MatchSelections,
                                 lazy='joined')

    __table_args__ = (UniqueConstraint('home_id', 'away_id', 'start_time',
                                       name='uq_duplicate_match_home_venue'),
                      UniqueConstraint('home_id', 'start_time',
                                       name='uq_home_fixture'),
                      UniqueConstraint('away_id', 'start_time',
                                       name='uq_away_fixture'),
                      CheckConstraint('home_id != away_id',
                                      name='different_teams_check')
                      )

    def __init__(self, home_id: int = None, away_id: int = None,
                 start_time: datetime = None, result: bool = False,
                 score_home: int = 0, score_away: int = 0,
                 selections: list = []):
        self.home_id = home_id
        self.away_id = away_id
        self.start_time = start_time
        self.result = result
        self.score_home = score_home
        self.score_away = score_away
        self.selections = selections

    @staticmethod
    def is_valid_entity(entity: dict, attribs: list = None) -> dict:
        """
        Validate and sanitise a match dict
        :param entity:      entity to check
        :param attribs:     attributes to check
        :return: Sanitised dict
        """
        if attribs is None:
            attribs = [M_HOME_ID, M_AWAY_ID, M_START_TIME, M_RESULT,
                       M_SCORE_HOME, M_SCORE_AWAY, M_SELECTIONS]

        # Check all data is valid
        _check_correct_type(entity, 'match', dict)
        valid_entity = {}
        for name, obj_type in MATCH_VARS_AND_TYPES:
            if name in attribs:
                obj = entity[name] if name in entity.keys() else None
                _check_correct_type(obj, name, obj_type)

                if obj_type == int:
                    if name in [M_HOME_ID, M_AWAY_ID] and obj < 1:
                        raise ModelError(HTTPStatus.UNPROCESSABLE_ENTITY,
                                         f"Invalid {name} value")
                    elif name in [M_SCORE_HOME, M_SCORE_AWAY] and obj < 0:
                        raise ModelError(HTTPStatus.UNPROCESSABLE_ENTITY,
                                         f"Invalid {name} value")
                elif name == M_SELECTIONS:
                    for pid in obj:
                        if not isinstance(pid, int):
                            raise ModelError(
                                HTTPStatus.UNPROCESSABLE_ENTITY,
                                f"Invalid {name} value: {pid}")

                valid_entity[name] = obj

        return valid_entity

    @staticmethod
    def empty_entity(values: dict) -> dict:
        """
        Return an empty a match dict
        :param values:  values to add to base empty entity
        :return: Sanitised dict
        """
        valid_entity = {}
        for name, obj_type in MATCH_VARS_AND_TYPES:
            if name in values.keys():
                value = values[name]
            elif obj_type == int:
                value = 0
            elif name == M_SELECTIONS:
                value = []
            elif name == M_START_TIME:
                value = datetime.now()
            elif name == M_RESULT:
                value = False
            else:
                value = None

            valid_entity[name] = value

        return valid_entity

    @staticmethod
    def from_dict(entity: dict):
        """
        Create a Match model from a dict.
        :param entity: dict to create from
        :return: new model
        """
        valid_match = Match.is_valid_entity(entity)

        match = Match(**valid_match)

        return match

    def __repr__(self):
        attributes = ''
        for k, v in self.get_dict().items():
            if len(attributes) > 0:
                attributes = f'{attributes}, '
            attributes = f'{attributes}{k}={v}'
        return f"<Match({attributes})>"


AnyModel = NewType('AnyModel', Union[Role, User, Team, Match])


def add_pre_configured():
    """
    Add preconfigured entities to database.
    """
    with db_session() as session:
        # pre-populate roles
        for role in PRE_CONFIG_ROLE_NAMES:
            session.add(Role(role))
        # pre-populate teams
        session.add(Team(UNASSIGNED_TEAM_NAME))
        session.commit()
