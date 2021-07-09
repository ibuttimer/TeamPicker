from datetime import datetime
import re
import typing as t

from flask.json import JSONEncoder, JSONDecoder
from dateutil.parser import parse

from .models_misc import MultiDictMixin

# Application date pattern is 'YYYY-MM-DDTHH:MM:SS'
# Auth0 date pattern is 'YYY-MM-DDTHH:MM:SS.fffZ'
__ISO8601_REGEX__ = re.compile(
    r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[\.\d{3,6}[\w]?]?',
    re.IGNORECASE)


class JsonEncoder(JSONEncoder):
    """
    The application JSON encoder. Handles extra types compared to the
    flask default encoder.

    -   :class:`datetime.datetime` and :class:`datetime.date` are
        serialized to ISO 8601 format, YYYY-MM-DDTHH:MM:SS.
    -   :class:`MultiDictMixin` is serialized to a dict string.

    Assign a subclass of this to :attr:`flask.Flask.json_encoder` or
    :attr:`flask.Blueprint.json_encoder` to override the default.
    """

    def default(self, o: t.Any) -> t.Any:
        """Convert ``o`` to a JSON serializable type. See
        :meth:`json.JSONEncoder.default`. Python does not support
        overriding how basic types like ``str`` or ``list`` are
        serialized, they are handled before this method.
        """
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, MultiDictMixin):
            return str(o.get_dict())
        return super().default(o)


class JsonDecoder(JSONDecoder):
    """
    Custom JSON decoder to convert ISO 8601 datetime strings to datetime
    objects.
    Based on https://stackoverflow.com/a/36379069
    """
    def __init__(self, *args, **kwargs):
        # Store original object_hook
        self.orig_obj_hook = kwargs.pop("object_hook", None)
        super(JsonDecoder, self).__init__(
            *args, object_hook=self.custom_obj_hook, **kwargs)

    def custom_obj_hook(self, dct: dict):
        for k, v in dct.items():
            if isinstance(v, str) and __ISO8601_REGEX__.match(v):
                dct[k] = parse(v)

        return self.orig_obj_hook(dct) if self.orig_obj_hook else dct
