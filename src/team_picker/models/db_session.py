from contextlib import contextmanager
from http import HTTPStatus

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import scoped_session
from werkzeug.exceptions import ServiceUnavailable

from ..util import print_exc_info
from ..util.exception import AbortError

db = SQLAlchemy()


@contextmanager
def db_session() -> scoped_session:
    """Provide a transactional scope around a series of operations."""
    try:
        yield db.session
        db.session.commit()

    except SQLAlchemyError as e:
        db.session.rollback()
        print_exc_info()
        if isinstance(e, IntegrityError):
            raise AbortError(HTTPStatus.UNPROCESSABLE_ENTITY,
                             "Conflicts with existing entry or "
                             "constraint condition not met") from e
        raise ServiceUnavailable() from e

    finally:
        db.session.close()
