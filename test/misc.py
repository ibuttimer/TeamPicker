import re
import urllib.request
import urllib.parse
from copy import deepcopy
from enum import Enum

# Regex to match parameters in url templates.
__REGEX_CONVERTER__ = re.compile(r'.?(<(string|int|float):(\w+)>)',
                                 re.IGNORECASE)


def make_url(base_url: str, **kwargs):
    """
    Make a url
    :param base_url:    base url
    :param kwargs:      key/value pairs for parameters and arguments
    :return:
    """
    url = base_url
    args = deepcopy(kwargs)
    for match in __REGEX_CONVERTER__.finditer(base_url):
        if match.group(3) in args.keys():
            url = url.replace(match.group(1), str(args.pop(match.group(3))))
            # args.pop(match.group(3))
            # args = {k: v for k, v in kwargs.items() if k != match.group(3)}

    params = urllib.parse.urlencode(args)
    return f'{url}?{params}' if args is not None and len(args) > 0 else url


class MatchParam(Enum):
    IGNORE = 1              # don't try to match

    CASE_SENSITIVE = 2      # case sensitive match
    CASE_INSENSITIVE = 3    # case insensitive match
    TRUE = 4                # match true
    FALSE = 5               # match false
    EQUAL = 6               # match equal
    NOT_EQUAL = 7           # match not equal
    IN = 8                  # match expected in value
    NOT_IN = 9              # match expected not in value

    ALL = 30                # match all
    NONE = 31               # match none
    COUNT = 32              # match specified count

    TO_INT = 50             # convert to int

    def __eq__(self, other):
        if self.__class__.__name__ == other.__class__.__name__ and isinstance(other, Enum):
            return self.value == other.value
        return NotImplemented


class Expect(Enum):
    SUCCESS = 1
    FAILURE = 2


class UserType(Enum):
    UNAUTHORISED = 1    # Unauthorised, no authorisation header.
    PUBLIC = 2          # Public, empty authorisation header.
    PLAYER = 3
    MANAGER = 4

