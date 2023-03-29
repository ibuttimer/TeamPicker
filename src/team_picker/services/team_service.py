from ..constants import (
    RESULT_ONE_TEAM, RESULT_UPDATED_COUNT, UNASSIGNED_TEAM_NAME
)
from ..models import ResultType, Team, M_ID, M_NAME, entity_to_dict
from .base_service import (get_all, get_by_id, create_entity, delete_by_id,
                           exists_by_id, update_entity, get_one
                           )


def get_all_teams(result_type: ResultType = ResultType.DICT):
    """
    Get all teams.
    :param result_type: type of result required, one of ResultType
    :return: list of all teams.
    """
    return get_all(Team, result_type=result_type)


def get_all_team_names():
    """
    Get all team names.
    :return: list of all team names.
    """
    return [entity_to_dict(t)[M_NAME] for t in get_all(
        Team, with_entities=Team.name, result_type=ResultType.MODEL)]


def get_team_by_id(team_id: int, result_type: ResultType = ResultType.DICT):
    """
    Get a team by id.
    :param team_id:     id of team to get
    :param result_type: type of result required, one of ResultType
    :return: team
    """
    return get_by_id(Team, team_id, result_type=result_type)


def get_team_by_name(name: str, result_type: ResultType = ResultType.DICT):
    """
    Get a team by name.
    :param name:     name of team to get
    :param result_type: type of result required, one of ResultType
    :return: team
    """
    return get_one(Team, criteria=Team.name == name, result_type=result_type)


def team_exists(team_id: int):
    """
    Check if a team exists by id.
    :param team_id:     id of team to check
    :return: True if exists otherwise False
    """
    return exists_by_id(Team, team_id)


def create_team(entity: dict, result_type: ResultType = ResultType.DICT):
    """
    Create a team.
    :param entity:      entity value dict
    :param result_type: type of result required, one of ResultType
    :return: created result {
        "created": <number of affected entities>,
        "id": <id of new entity>
        "team": <new entity>
    }
    """
    return create_entity(Team.from_dict, entity, RESULT_ONE_TEAM,
                         result_type=result_type)


def delete_team_by_id(team_id: int):
    """
    Delete a team by id.
    :param team_id: id of team to delete
    :return: deleted result {
        "deleted": <number of affected entities>
    }
    """
    return delete_by_id(Team, team_id)


def update_team(team_id: int, updates: dict,
                result_type: ResultType = ResultType.DICT):
    """
    Update a team.
    :param team_id:     id of team to update
    :param updates:     updates to apply
    :param result_type: type of result required, one of ResultType
    :return: updated result {
        "updated": <number of affected entities>,
        "team": <updated entity>
    }
    """
    result = update_entity(Team, Team.is_valid_entity(updates),
                           criteria=Team.id == team_id)
    if result[RESULT_UPDATED_COUNT] > 0:
        result[RESULT_ONE_TEAM] = get_team_by_id(
            team_id, result_type=result_type)

    return result


def get_unassigned_team_id() -> int:
    """
    Get team id of the unassigned team.
    :return: team id
    """
    unassigned = get_team_by_name(UNASSIGNED_TEAM_NAME)
    return unassigned[M_ID]


def is_unassigned_team(team_id: int) -> bool:
    """
    Check if the specified team id represents the unassigned team.
    :param team_id: team id to check
    :return: team
    """
    return team_id == get_unassigned_team_id()


def get_team_name(team_id: int):
    """
    Get name of team by id.
    :param team_id:     id of team to get
    :return: team name
    """
    team = get_one(Team, with_entities=Team.name, criteria=Team.id == team_id,
                   result_type=ResultType.DICT)
    return team[M_NAME] if team is not None else None



