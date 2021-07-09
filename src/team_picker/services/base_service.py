from typing import Callable

from sqlalchemy.orm import scoped_session

from ..constants import (RESULT_CREATED_COUNT, RESULT_DELETED_COUNT,
                         RESULT_UPDATED_COUNT
                         )
from ..models import db_session, ResultType, M_ID, AnyModel


def build_query(base_query, with_entities=None, criteria=None,
                order_by=None):
    """
    Get an entity.
    :param base_query:    base query
    :param with_entities: model entities to return
    :param criteria:      entity filter criteria
    :param order_by:      order results by
    :return: entity
    """
    query = base_query
    if with_entities is not None:
        query = query.with_entities(with_entities)
    if criteria is not None:
        query = query.filter(criteria)
    if order_by is not None:
        query = query.order_by(order_by)

    return query


def get_all(model: AnyModel,
            with_entities=None, criteria=None, order_by=None,
            result_type: ResultType = ResultType.DICT):
    """
    Get all teams.
    :param model:       model to query
    :param with_entities: model entities to return
    :param criteria:      entity filter criteria
    :param order_by:      order results by
    :param result_type: type of result required, one of ResultType
    :return: list of all entities.
    """
    with db_session() as session:
        entities = build_query(session.query(model),
                               with_entities=with_entities,
                               criteria=criteria,
                               order_by=order_by)\
            .all()
        if result_type == ResultType.DICT:
            entities = [e.get_dict() for e in entities]

    return entities


def get_by_id_raw(session: scoped_session, model: AnyModel, entity_id: int):
    """
    Get an entity.
    :param session:
    :param model:       model to query
    :param entity_id:   id of entity to get
    :return: entity
    """
    return session.query(model).filter(model.id == entity_id).first()


def get_one(model: AnyModel,
            with_entities=None, criteria=None,
            result_type: ResultType = ResultType.DICT):
    """
    Get an entity.
    :param model:       model to query
    :param with_entities: model entities to return
    :param criteria:      entity filter criteria
    :param result_type: type of result required, one of ResultType
    :return: entity
    """
    with db_session() as session:
        entity = build_query(session.query(model),
                             with_entities=with_entities,
                             criteria=criteria) \
            .first()
        if entity is not None and result_type == ResultType.DICT:
            if with_entities is None:
                entity = entity.get_dict()

    return entity


def get_by_id(model: AnyModel, entity_id: int,
              result_type: ResultType = ResultType.DICT):
    """
    Get an entity by id.
    :param model:       model to query
    :param entity_id:   id of entity to get
    :param result_type: type of result required, one of ResultType
    :return: entity
    """
    return get_one(model, criteria=model.id == entity_id,
                   result_type=result_type)


def exists_by_id(model: AnyModel, entity_id: int):
    """
    Check if an entity exists by id.
    :param model:       model to query
    :param entity_id:   id of entity to check
    :return: True if exists otherwise False
    """
    with db_session() as session:
        entity = session.query(model) \
            .with_entities(model.id) \
            .filter(model.id == entity_id) \
            .first()
        exists = entity is not None

    return exists


def create_entity(from_dict: Callable, entity: dict, key: str,
                  result_type: ResultType = ResultType.DICT,
                  preprocess: Callable = None):
    """
    Create an entity.
    :param from_dict:   function to create model object
    :param entity:      entity value dict
    :param key:         key for created entity in result
    :param result_type: type of result required, one of ResultType
    :param preprocess:  callable to preprocess entity
    :return: created result {
        "created": <number of affected entities>,
        "id": <id of new entity>
        key: <new entity>
    }
    """
    with db_session() as session:
        model = from_dict(entity)
        if preprocess is not None:
            preprocess(session, model)
        session.add(model)
        session.flush()  # Flush to populate id.
        entity_id = model.id
        entity = model.get_dict() if result_type == ResultType.DICT else model

    return {
        RESULT_CREATED_COUNT: 1,
        M_ID: entity_id,
        key: entity
    }


def delete_entity(model: AnyModel, criteria=None):
    """
    Delete entities.
    :param model:       SQLAlchemy model
    :param criteria:    entity filter criteria
    :return: deleted result {
        "deleted": <number of affected entities>
    }
    """
    with db_session() as session:
        delete_query = session.query(model)
        if criteria is not None:
            delete_query = delete_query.filter(criteria)

        count = delete_query.count()  # Number of rows that will be affected.
        if count > 0:
            delete_query.delete()

    return {
        RESULT_DELETED_COUNT: count
    }


def delete_by_id(model: AnyModel, entity_id: int):
    """
    Delete an entity by id.
    :param model:       SQLAlchemy model
    :param entity_id:   id of entity to delete
    :return: number of affected entities
    """
    return delete_entity(model, criteria=model.id == entity_id)


def update_entity(model: AnyModel, updates: dict, criteria=None):
    """
    Update an entity.
    :param model:       SQLAlchemy model
    :param updates:     updates to apply
    :param criteria:    entity filter criteria
    :return: updated result {
        "updated": <number of affected entities>
    }
    """
    with db_session() as session:
        update_query = session.query(model)
        if criteria is not None:
            update_query = update_query.filter(criteria)

        count = update_query.count()  # Number of rows that will be affected.
        if count > 0:
            update_query.update(updates, synchronize_session="fetch")

    return {
        RESULT_UPDATED_COUNT: count
    }
