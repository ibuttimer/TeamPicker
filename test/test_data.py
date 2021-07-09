"""
Test data classes corresponding to database models.
"""
from copy import deepcopy
from datetime import datetime
from typing import List

from team_picker import MANAGER_ROLE, PLAYER_ROLE, UNASSIGNED_TEAM_NAME, \
    APP_DATETIME_FMT, MANAGER_ROLE_NAME, PLAYER_ROLE_NAME
from team_picker.models import Role, Team, User, Match, M_ID


class EqualDataMixin:
    """
    Mixin class to add dict entries equality test
    """
    def equals(self, other: dict, ignore: list = None, **kwargs):
        """
        Equality test
        :param other:   data to compare with
        :param ignore:  list of attributes to ignore
        :param kwargs:  key/value pairs of ignore lists for EqualDataMixin
                        sub attributes
        :return:
        """
        if ignore is None:
            ignore = []
        equal = isinstance(other, dict)
        if equal:
            for k, v in vars(self).items():
                if k not in ignore:
                    if isinstance(v, list):
                        equal = isinstance(other[k], list)
                        if equal:
                            sub_attrib_ignore = \
                                kwargs[k] if k in kwargs.keys() else []
                            v_list = [e.to_dict(ignore=sub_attrib_ignore)
                                      if isinstance(e, EqualDataMixin) else e
                                      for e in v]
                            equal = (v_list == other[k])
                    else:
                        sub_attrib_ignore = \
                            kwargs[k] if k in kwargs.keys() else []
                        equal = v.equals(other[k], ignore=sub_attrib_ignore) \
                            if isinstance(v, EqualDataMixin) \
                            else (v == other[k])
                    if not equal:
                        break
        return equal

    @staticmethod
    def _dict_value(v):
        """ Get the dict value """
        dict_v = v  # Default, value as is.
        if isinstance(v, list):
            # Make a list of values or EqualDataMixin dicts as appropriate.
            dict_v = [e if not isinstance(e, EqualDataMixin) else e.to_dict()
                      for e in v]
        elif isinstance(v, EqualDataMixin):
            # Make EqualDataMixin dict.
            dict_v = v.to_dict()

        return dict_v

    def to_dict(self, ignore: list = None):
        """
        Convert to a dict.
        :param ignore:  list of attributes to ignore
        :return:
        """
        if ignore is None:
            ignore = []
        return {
            k: self._dict_value(v)
            for k, v in vars(self).items() if k not in ignore
        }


def repr_data_class(obj: EqualDataMixin):
    """
    Generate string representation of specified object.
    :param obj:
    :return:
    """
    attributes = ''
    for k, v in obj.to_dict().items():
        if len(attributes) > 0:
            attributes = f'{attributes}, '
        attributes = f'{attributes}{k}={v}'
    return f"<{type(obj).__name__}({attributes})>"


ENTITY_ID = "entity_id"


class RoleData(EqualDataMixin):
    """
    Data class representing a role.
    :param entity_id:   role id
    :param role:        name of role
    """
    def __init__(self, entity_id: int, role: str):
        self.id = entity_id
        self.role = role

    def to_model(self, ignore: list = None):
        """
        Convert to a Role.
        :param ignore:  list of attributes to ignore
        :return:
        """
        return Role(**self.to_dict(ignore=ignore))

    def __repr__(self):
        return repr_data_class(self)


class TeamData(EqualDataMixin):
    """
    Data class representing a team.
    :param entity_id:   team id
    :param name:        name of team
    """
    def __init__(self, entity_id: int, name: str):
        self.id = entity_id
        self.name = name

    def to_model(self, ignore: list = None):
        """
        Convert to a Team.
        :param ignore:  list of attributes to ignore
        :return:
        """
        return Team(**self.to_dict(ignore=ignore))

    def __repr__(self):
        return repr_data_class(self)


class UserData(EqualDataMixin):
    """
    Data class representing a user.
    :param entity_id:   user id
    :param name:        name of user
    """
    def __init__(self, entity_id: int, name: str = None, surname: str = None,
                 auth0_id: str = None, role_id: int = None,
                 team_id: int = None):
        self.id = entity_id
        self.name = name
        self.surname = surname
        self.auth0_id = auth0_id
        self.role_id = role_id
        self.team_id = team_id

    def to_model(self, ignore: list = None):
        """
        Convert to a User.
        :param ignore:  list of attributes to ignore
        :return:
        """
        return User(**self.to_dict(ignore=ignore))

    def __repr__(self):
        return repr_data_class(self)


class MatchData(EqualDataMixin):
    """
    Data class representing a match.
    :param entity_id:   match id
    :param home_id:     id of home team
    :param away_id:     id of away team
    :param start_time:  start time
    :param result:      finalised result flag
    :param score_home:  home team score
    :param score_away:  away team score
    :param selections:  selections
    """
    def __init__(self, entity_id: int, home_id: int = None, away_id: int = None,
                 start_time: datetime = None, result: bool = False,
                 score_home: int = None, score_away: int = None,
                 selections=None):
        if selections is None:
            selections = []
        self.id = entity_id
        self.home_id = home_id
        self.away_id = away_id
        self.start_time = start_time
        self.result = result
        self.score_home = score_home
        self.score_away = score_away
        self.selections = selections

    def to_model(self, ignore: list = None):
        """
        Convert to a Match.
        :param ignore:  list of attributes to ignore
        :return:
        """
        return Match(**self.to_dict(ignore=ignore))

    @staticmethod
    def from_dict(from_dict: dict):
        std_dict = deepcopy(from_dict)
        entity_id = 0
        if M_ID in std_dict.keys():
            entity_id = std_dict.pop(M_ID)
        if ENTITY_ID not in std_dict.keys():
            std_dict[ENTITY_ID] = entity_id

        return MatchData(**std_dict)

    def strf_start_time(self):
        return self.start_time.strftime(APP_DATETIME_FMT)

    def __repr__(self):
        return repr_data_class(self)


# Predefined application roles.
ROLES = {
    MANAGER_ROLE: RoleData(0, MANAGER_ROLE_NAME),
    PLAYER_ROLE: RoleData(0, PLAYER_ROLE_NAME)
}

# Predefined application team.
UNASSIGNED_TEAM = TeamData(0, UNASSIGNED_TEAM_NAME)


def get_role_from_id(role_id: int):
    """
    Get the role name for the specified id
    :param role_id: id of role
    :return:
    """
    role = ''
    for k, v in ROLES.items():
        if v.id == role_id:
            role = k
            break
    return role
