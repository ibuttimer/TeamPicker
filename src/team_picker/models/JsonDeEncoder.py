from datetime import datetime
import re
import typing as t
import json
import uuid
import decimal
import dataclasses
from datetime import date

from dateutil.parser import parse
from flask.json.provider import DefaultJSONProvider

from werkzeug.http import http_date

from .models_misc import MultiDictMixin

# Application date pattern is 'YYYY-MM-DDTHH:MM:SS'
# Auth0 date pattern is 'YYY-MM-DDTHH:MM:SS.fffZ'
__ISO8601_REGEX__ = re.compile(
    r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[\.\d{3,6}[\w]?]?',
    re.IGNORECASE)


def _default(o: t.Any) -> t.Any:
    """
    Default json implementation copied from flask/json/provider.py with
    additions
    :param o: object to jsonify
    :return:
    """
    # custom additions
    if isinstance(o, datetime):
        return o.isoformat()
    if isinstance(o, MultiDictMixin):
        return str(o.get_dict())

    # original implementation
    if isinstance(o, date):
        return http_date(o)

    if isinstance(o, (decimal.Decimal, uuid.UUID)):
        return str(o)

    if dataclasses and dataclasses.is_dataclass(o):
        return dataclasses.asdict(o)

    if hasattr(o, "__html__"):
        return str(o.__html__())

    raise TypeError(
        f"Object of type {type(o).__name__} is not JSON serializable")


def _custom_decode(dct: dict, obj_hook: t.Callable = None):
    """
    Custom object_hook to implement custom decoders.
    :param dct: object literal decode
    :param obj_hook: object_hook function: default None
    :return:
    """
    for k, v in dct.items():
        if isinstance(v, str) and __ISO8601_REGEX__.match(v):
            dct[k] = parse(v)

    return obj_hook(dct) if obj_hook else dct


class TPDefaultJSONProvider(DefaultJSONProvider):
    """Provide JSON operations using Python's built-in :mod:`json`
    library. Serializes the following additional data types:

    -   :class:`datetime.datetime` and :class:`datetime.date` are
        serialized to :rfc:`822` strings. This is the same as the HTTP
        date format.
    -   :class:`uuid.UUID` is serialized to a string.
    -   :class:`dataclasses.dataclass` is passed to
        :func:`dataclasses.asdict`.
    -   :class:`~markupsafe.Markup` (or any object with a ``__html__``
        method) will call the ``__html__`` method to get a string.
    """

    default: t.Callable[[t.Any], t.Any] = staticmethod(
        _default
    )  # type: ignore[assignment]
    """Apply this function to any object that :meth:`json.dumps` does
    not know how to serialize. It should return a valid JSON type or
    raise a ``TypeError``.
    """

    def dumps(self, obj: t.Any, **kwargs: t.Any) -> str:
        """Serialize data as JSON to a string.

        Keyword arguments are passed to :func:`json.dumps`. Sets some
        parameter defaults from the :attr:`default`,
        :attr:`ensure_ascii`, and :attr:`sort_keys` attributes.

        :param obj: The data to serialize.
        :param kwargs: Passed to :func:`json.dumps`.
        """
        kwargs.setdefault("default", self.default)
        kwargs.setdefault("ensure_ascii", self.ensure_ascii)
        kwargs.setdefault("sort_keys", self.sort_keys)
        return json.dumps(obj, **kwargs)

    def loads(self, s: str | bytes, **kwargs: t.Any) -> t.Any:
        """Deserialize data as JSON from a string or bytes.

        :param s: Text or UTF-8 bytes.
        :param kwargs: Passed to :func:`json.loads`.
        """
        kwargs.setdefault("object_hook", _custom_decode)
        return json.loads(s, **kwargs)
