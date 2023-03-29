from enum import IntEnum, auto
from http import HTTPStatus
from typing import Union

from flask import request
from sqlalchemy import and_, desc, asc, or_, select, func
from sqlalchemy.orm import scoped_session

from .user_service import get_user_by_id_raw
from ..constants import (RESULT_UPDATED_COUNT, RESULT_ONE_MATCH,
                         ORDER_DATE_DESC, ORDER_DATE_ASC, OPPOSITION,
                         DATE_RANGE, NO_ARG, YES_ARG, SELECT_QUERY, MAYBE_ARG,
                         TOGGLE_ARG, TEAM
                         )
from ..util import (
    NO_OPTION_SELECTED, DateRange, NO_STATUS, CONFIRMED_STATUS,
    NOT_AVAILABLE_STATUS, MAYBE_STATUS
)
from ..models import (ResultType, Match, M_SELECTIONS, M_ID, M_START_TIME,
                      db_session, M_AWAY_ID, M_HOME_ID, MatchSelections,
                      M_CONFIRMED
                      )
from ..models.exception import ModelError
from .base_service import (get_all, get_by_id, exists_by_id, create_entity,
                           delete_by_id, update_entity, get_one
                           )


def standardise_match(match: Union[Match, dict]) -> Union[Match, dict]:
    """
    Standardise match in preparation for returning result.
    :param match: match to standardise
    :return:
    """
    # Standardise selections by ensuring they are in ascending player id order.
    if isinstance(match, dict):
        if M_SELECTIONS in match.keys():
            match[M_SELECTIONS].sort(key=lambda s: s[M_ID])
    else:
        match.selections.sort(key=lambda s: s.id)
    return match


def get_all_matches(order_by: str = None, criteria: dict = None,
                    result_type: ResultType = ResultType.DICT):
    """
    Get all matches.
    :param order_by:    order results by
    :param criteria:    filter criteria
    :param result_type: type of result required, one of ResultType
    :return: list of all matches.
    """
    if order_by is None:
        order_by = ''
    if order_by.lower() == ORDER_DATE_DESC:
        order = desc(Match.start_time)
    elif order_by.lower() == ORDER_DATE_ASC:
        order = asc(Match.start_time)
    else:
        order = None

    if criteria is not None:
        search_criteria = []

        if TEAM in criteria.keys():
            team = criteria[TEAM]
            if team != NO_OPTION_SELECTED:
                search_criteria.append(
                    or_(Match.home_id == team, Match.away_id == team)
                )

        if OPPOSITION in criteria.keys():
            opposition = criteria[OPPOSITION]
            if opposition != NO_OPTION_SELECTED:
                search_criteria.append(
                    or_(
                        Match.home_id == opposition, Match.away_id == opposition
                    )
                )

        if DATE_RANGE in criteria.keys() and M_START_TIME in criteria.keys():
            date_criteria = None
            date_range = criteria[DATE_RANGE]
            start_time = func.date(criteria[M_START_TIME])
            if date_range == DateRange.BEFORE_DATE:
                date_criteria = func.date(Match.start_time) < start_time
            elif date_range == DateRange.BEFORE_OR_EQUAL_DATE:
                date_criteria = func.date(Match.start_time) <= start_time
            elif date_range == DateRange.EQUAL_DATE:
                date_criteria = func.date(Match.start_time) == start_time
            elif date_range == DateRange.AFTER_OR_EQUAL_DATE:
                date_criteria = func.date(Match.start_time) >= start_time
            elif date_range == DateRange.AFTER_DATE:
                date_criteria = func.date(Match.start_time) > start_time

            if date_criteria is not None:
                search_criteria.append(date_criteria)

        if len(search_criteria) > 1:
            criteria = and_(*search_criteria)
        elif len(search_criteria) == 1:
            criteria = search_criteria[0]
        else:
            criteria = None

    return [standardise_match(match)
            for match in get_all(Match, criteria=criteria, order_by=order,
                                 result_type=result_type)
            ]


def get_match_by_id(match_id: int, result_type: ResultType = ResultType.DICT):
    """
    Get a match.
    :param match_id: id of match to get
    :param result_type: type of result required, one of ResultType
    :return: match
    """
    match = get_by_id(Match, match_id, result_type=result_type)
    return standardise_match(match) if match is not None else match


def get_match_by_id_and_team(match_id: int, team_id: int,
                             result_type: ResultType = ResultType.DICT):
    """
    Get a match.
    :param match_id: id of match to get
    :param team_id: id of match team
    :param result_type: type of result required, one of ResultType
    :return: match
    """
    match = get_one(Match, criteria=and_(
        Match.id == match_id, or_(
            Match.home_id == team_id, Match.away_id == team_id)),
                    result_type=result_type)
    return standardise_match(match) if match is not None else match


def match_exists(match_id: int):
    """
    Check if a match exists by id.
    :param match_id:     id of match to check
    :return: True if exists otherwise False
    """
    return exists_by_id(Match, match_id)


def preprocess_match(session: scoped_session, model: Match):
    """
    Preprocess a match for addition to the database.
    :param session: current session
    :param model:   match to preprocess
    """
    # Convert user ids to entities.
    model.selections = [
        get_user_by_id_raw(session, uid) for uid in model.selections
    ]


_HOME_AWAY_START_ = [M_START_TIME, M_HOME_ID, M_AWAY_ID]


def verify_match(entity: dict, match_id: int = None):
    """
    Verify a match is valid.
    :param entity: Entity to check
    :param match_id: id of match if update operation
    """
    if match_id is not None:
        match = get_match_by_id(match_id, result_type=ResultType.DICT)
        old = {
            M_START_TIME: match.start_time,
            M_HOME_ID: match.home_id,
            M_AWAY_ID: match.away_id
        }
    else:
        old = {k: None for k in _HOME_AWAY_START_}

    with db_session() as session:
        new = {
            k: entity[k] if entity[k] is not None else None
            for k in _HOME_AWAY_START_
        }
        # Verify conditions the database constraints can't check.
        # Ensure no home/away/time conflict
        check = {
            k: new[k] if new[k] is not None else old[k]
            for k in _HOME_AWAY_START_
        }
        if check[M_START_TIME] is not None and check[M_HOME_ID] is not None \
                and check[M_AWAY_ID] is not None:
            # Ensure no home team away/time conflict
            count = session.query(Match) \
                .filter(and_(
                    Match.start_time == check[M_START_TIME],
                    Match.away_id == check[M_HOME_ID]
                )).count()
            if count > 0:
                raise ModelError(HTTPStatus.UNPROCESSABLE_ENTITY,
                                 f"Away fixture conflict for Home team")
            # Ensure no away team home/time conflict
            count = session.query(Match) \
                .filter(and_(
                    Match.start_time == check[M_START_TIME],
                    Match.home_id == check[M_AWAY_ID],
                )).count()
            if count > 0:
                raise ModelError(HTTPStatus.UNPROCESSABLE_ENTITY,
                                 f"Home fixture conflict for Away team")

            # Verify database constraints.
            # Ensure no duplicate fixture.
            count = session.query(Match) \
                .filter(and_(
                    Match.start_time == check[M_START_TIME],
                    Match.home_id == check[M_AWAY_ID],
                    Match.away_id == check[M_HOME_ID]
                )).count()
            if count > 0:
                raise ModelError(HTTPStatus.UNPROCESSABLE_ENTITY,
                                 f"Duplicate fixture exists")
            # Ensure no home team home/time conflict
            count = session.query(Match) \
                .filter(and_(
                    Match.start_time == check[M_START_TIME],
                    Match.home_id == check[M_HOME_ID],
                )).count()
            if count > 0:
                raise ModelError(HTTPStatus.UNPROCESSABLE_ENTITY,
                                 f"Home fixture conflict for Home team")
            # Ensure no away team away/time conflict
            count = session.query(Match) \
                .filter(and_(
                    Match.start_time == check[M_START_TIME],
                    Match.away_id == check[M_AWAY_ID],
                )).count()
            if count > 0:
                raise ModelError(HTTPStatus.UNPROCESSABLE_ENTITY,
                                 f"Away fixture conflict for Away team")


def create_match(entity: dict, result_type: ResultType = ResultType.DICT):
    """
    Create a match.
    :param entity:      entity value dict
    :param result_type: type of result required, one of ResultType
    :return: created result {
        "created": <number of affected entities>,
        "id": <id of new entity>
        "match": <new entity>
    }
    """
    verify_match(entity)
    created = create_entity(Match.from_dict, entity, RESULT_ONE_MATCH,
                            result_type=result_type,
                            preprocess=preprocess_match)
    standardise_match(created[RESULT_ONE_MATCH])
    return created


def delete_match_by_id(match_id: int):
    """
    Delete a match by id.
    :param match_id: id of match to delete
    :return: deleted result {
        "deleted": <number of affected entities>
    }
    """
    return delete_by_id(Match, match_id)


def remove_selections(criteria) -> int:
    """
    Remove match selections.
    :param criteria: criteria to filter by
    :return:
    """
    with db_session() as session:
        # Remove selections.
        query = MatchSelections.select().filter(criteria)
        delete = session.execute(query).scalar()
        if delete is not None and delete > 0:
            session.execute(
                MatchSelections.delete().filter(criteria)
            )
        else:
            delete = 0

    return delete


def add_selections(match_id: int, selections: Union[list, int]):
    """
    Add match selections.
    :param match_id:   id of match to update
    :param selections: id(s) of
    :return: updated result {
        "updated": <number of affected entities>,
        "match": <updated entity>
    }
    """
    with db_session() as session:
        # Add new selections.
        added = 0
        for uid in selections if isinstance(selections, list) else [selections]:
            session.execute(
                MatchSelections.insert().values(
                    match_id=match_id, user_id=uid, confirmed=NO_STATUS)
            )
            added = added + 1

    return added


def update_match(match_id: int, updates: dict,
                 result_type: ResultType = ResultType.DICT):
    """
    Update a match.
    :param match_id:     id of match to update
    :param updates:     updates to apply
    :param result_type: type of result required, one of ResultType
    :return: updated result {
        "updated": <number of affected entities>,
        "match": <updated entity>
    }
    """
    valid_updates = Match.is_valid_entity(updates, attribs=updates.keys())
    result = {}

    # Process selection changes
    selections = valid_updates.pop(M_SELECTIONS, None)
    if selections is not None:
        with db_session() as session:
            # Remove old selections.
            delete = remove_selections(MatchSelections.c.match_id == match_id)

            # Add new selections.
            added = add_selections(match_id, selections)

            if delete > 0 or added > 0:
                result[RESULT_UPDATED_COUNT] = 1

    if len(valid_updates.keys()) > 0:
        result.update(update_entity(Match, valid_updates,
                                    criteria=Match.id == match_id))

    if result[RESULT_UPDATED_COUNT] > 0:
        result[RESULT_ONE_MATCH] = standardise_match(
            get_match_by_id(match_id, result_type=result_type)
        )

    return result


def player_selected_criteria(match_id: int, user_id: int):
    """
    Criteria to filter matches based on match and user ids.
    :param match_id: id of match
    :param user_id: id of user
    :return:
    """
    return and_(MatchSelections.c.match_id == match_id,
                MatchSelections.c.user_id == user_id)


def is_selected(match_id: int, user_id: int):
    """
    Check if the a user is selected for a match
    :param match_id: id of match
    :param user_id: id of user
    :return:
    """
    with db_session() as session:
        count = session.execute(
            MatchSelections.select().filter(
                player_selected_criteria(match_id, user_id)
            )
        ).scalar()
        selected = (count is not None and count > 0)

    return selected


def is_selected_and_confirmed(match_id: int, user_id: int):
    """
    Check if the a user is selected and confirmed for a match
    :param match_id: id of match
    :param user_id: id of user
    :return: tuple of selected status & confirmed status
    """
    selected = False
    confirmed = False
    with db_session() as session:
        query = MatchSelections.select().filter(
            player_selected_criteria(match_id, user_id)
        )
        selection = session.execute(query).first()
        if selection is not None:
            selection = selection._asdict()
            selected = True
            confirmed = selection[M_CONFIRMED]

    return selected, confirmed


def get_selected_and_unconfirmed(user_id: int):
    """
    Get the list of matches for which a user is selected but has not yet
    confirmed availability.
    :param user_id: id of user
    :return: tuple of selected status & confirmed status
    """
    with db_session() as session:
        # Need final filter statement to resolve cartesian products.
        query = \
            select(Match.id, Match.start_time, Match.home_id, Match.away_id) \
            .select_from(Match)\
            .filter(
                and_(MatchSelections.c.user_id == user_id,
                     or_(MatchSelections.c.confirmed == NO_STATUS,
                         MatchSelections.c.confirmed == MAYBE_STATUS)
                     )
            )\
            .filter(Match.id == MatchSelections.c.match_id)

        matches = session.execute(query).all()

    return matches


class SelectChoice(IntEnum):
    YES = auto()
    NO = auto()
    MAYBE = auto()
    TOGGLE = auto()

    @staticmethod
    def from_request(dflt_value):
        """
        Get value from request query arguments.
        :param dflt_value: Default value if query not present
        :return: 
        """
        for chk_arg, chk_choice in SELECT_CHOICE_OPTIONS:
            if chk_choice == dflt_value:
                arg = chk_arg
                choice = chk_choice
                break
        else:
            arg = NO_ARG
            choice = SelectChoice.NO
        req_value = request.args.get(SELECT_QUERY, arg, type=str).lower()
        for chk_arg, chk_choice in SELECT_CHOICE_OPTIONS:
            if chk_arg == req_value:
                choice = chk_choice
                break
        return choice


SELECT_CHOICE_OPTIONS = [
    (YES_ARG, SelectChoice.YES),
    (NO_ARG, SelectChoice.NO),
    (MAYBE_ARG, SelectChoice.MAYBE),
    (TOGGLE_ARG, SelectChoice.TOGGLE),
]


def set_selection(match_id: int, user_id: int,
                  choice: SelectChoice = SelectChoice.TOGGLE):
    """
    Set a user's selection status for a match
    :param match_id: id of match
    :param user_id: id of user
    :param choice:
    """
    add = False
    remove = False
    selected = is_selected(match_id, user_id)
    if choice == SelectChoice.TOGGLE:
        if selected:
            remove = True
        else:
            add = True
    elif choice == SelectChoice.YES:
        if not selected:
            add = True
    elif choice == SelectChoice.NO:
        if selected:
            remove = True
    else:
        raise ValueError(f"Invalid choice option: {choice}")

    if add:
        add_selections(match_id, [user_id])
    elif remove:
        remove_selections(
            player_selected_criteria(match_id, user_id)
        )


def set_confirmation(match_id: int, user_id: int,
                     choice: SelectChoice = SelectChoice.MAYBE):
    """
    Set a user's confirmation status for a match
    :param match_id: id of match
    :param user_id: id of user
    :param choice:
    """
    with db_session() as session:
        if is_selected(match_id, user_id):

            if choice == SelectChoice.NO:
                confirmed = NOT_AVAILABLE_STATUS
            elif choice == SelectChoice.MAYBE:
                confirmed = MAYBE_STATUS
            elif choice == SelectChoice.YES:
                confirmed = CONFIRMED_STATUS
            else:
                raise ValueError(f"Invalid choice option: {choice}")

            updated = session.execute(
                MatchSelections.update().filter(
                    player_selected_criteria(match_id, user_id)
                ).values(confirmed=confirmed)
            )

            if updated is not None:
                pass

