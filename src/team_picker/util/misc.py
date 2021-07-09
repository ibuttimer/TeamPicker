import os
import traceback
from datetime import datetime

from dateutil import tz
from dateutil.parser import parse
from http import HTTPStatus
from typing import Any, Optional

from flask import jsonify, Response

from .forms_misc import HOME_VENUE

from ..auth.exception import AuthError
from ..util.exception import AppError


def _make_result(success: bool, error: int = None, message: str = None,
                 **kwargs) -> Response:
    """
    Make a json result.
    :param success: True or False
    :param error:   if success == False, HTTP error code
    :param message: if success == False, HTTP error message
    :param kwargs:  result data as key/value pairs
    :return: Response
    """
    result = {
        'success': success
    }
    if error is not None:
        result["error"] = error
        result["message"] = message if message is not None else ''

    result = {**result, **kwargs}

    return jsonify(result)


def success_result(**kwargs):
    """
    Make a success json result.
    :param kwargs:  result data as key/value pairs
    :return:
    """
    return _make_result(True, **kwargs)


def error_result(error: int, message: str, **kwargs) -> Response:
    """
    Make a fail json result.
    :param error:   if success == False, HTTP error code
    :param message: if success == False, HTTP error message
    :param kwargs:  result data as key/value pairs
    :return:
    """
    return _make_result(False, error=error, message=message, **kwargs)


def http_error_result(http_code: HTTPStatus, error) -> (Response, int):
    """
    Make a fail json result.
    :param http_code:  HTTP status code
    :param error:      error exception
    :return:
    """
    extra = {}
    if isinstance(error, AuthError):
        if "error" in vars(error):
            extra = error.error
    elif isinstance(error, AppError):
        if error.error is not None:
            extra = {"detailed_message": error.error}
    elif isinstance(error, Exception):
        if "args" in vars(error):
            extra = {"detailed_message": error.args}

    return error_result(
        http_code.value, http_code.phrase, **extra), http_code.value


def print_exc_info():
    """ Print exception information. """
    for line in traceback.format_exc().splitlines():
        print(line)


def eval_environ_var_truthy(environ_var: str, dflt_val: bool = False) -> bool:
    """
    Evaluate if environment variable setting is truthy.
    :param environ_var: environment variable name
    :param dflt_val:    default value for variable, (default is false)
    :return True if environment variable is truthy else False
    """
    # Evaluate environment variable; f/false/n/no/0 are False,
    # t/true/y/yes/1 are True, otherwise use the truthy value.
    value = os.environ.get(environ_var)
    if value is not None:
        value = value.lower()
        if value in ['f', 'false', 'n', 'no']:
            value = False
        elif value in ['t', 'true', 'y', 'yes']:
            value = True
        else:
            if value.isnumeric():
                value = int(value)
            value = bool(value)
    else:
        value = dflt_val
    return value


def eval_environ_var_none(environ_var: str) -> Optional[str]:
    """
    Evaluate if environment variable setting is None.
    :param environ_var: environment variable name
    :return string if environment variable is not None else None
    """
    # Evaluate environment variable; ''/none/no are None
    value = os.environ.get(environ_var)
    if value is not None:
        test_value = value.lower()
        if test_value in ['', 'n', 'no', 'none']:
            value = None
    return value


def current_datetime():
    """ Current datetime to minute accuracy """
    return datetime.today().replace(second=0, microsecond=0)


def choose_by_a_b_or_else(a: Any, b: Any, a_value: Any, b_value: Any,
                          else_value: Any) -> Any:
    """
    Chose a result value, based on the result of condition a or b.
    :param a:  condition a
    :param b:  condition b
    :param a_value:  result value if condition a is truthy
    :param b_value:  result value if condition b is truthy
    :param else_value:  result value if neither condition a or b are truthy
    :return:
    """
    return a_value if a else (b_value if b else else_value)


def choose_by_ls_eq_gr(expected: int, actual: int, ls_value: Any, eq_value: Any,
                       gr_value: Any) -> Any:
    """
    Chose a result value, based on less than/equality/greater than result of
    test value and expected.
    :param expected:  expected value
    :param actual:   test value
    :param ls_value:  less than result value
    :param eq_value:  equal result value
    :param gr_value:  greater than result value
    :return:
    """
    return choose_by_a_b_or_else(actual < expected, actual > expected,
                                 ls_value, gr_value, eq_value)


def ternary_op(condition: Any, t_value: Any, f_value: Any) -> Any:
    """
    Choose a result value, based on the truthy result of a condition.
    :param condition:  test condition
    :param t_value:  result value if test condition is truthy
    :param f_value:  result value if test condition is not truthy
    :return:
    """
    return t_value if condition else f_value


def choose_by_eq(expected: int, actual: int, eq_value: Any,
                 neq_value: Any) -> Any:
    """
    Choose a result value, based on equality result of test value and expected.
    :param expected:  expected value
    :param actual:   test value
    :param eq_value:  equal result value
    :param neq_value:  not equal result value
    :return:
    """
    return ternary_op(actual == expected, eq_value, neq_value)


def choose_by_home_venue(home_venue: int, home_value: Any,
                         away_value: Any) -> Any:
    """
    Choose home or away value, based on home team id.
    :param home_venue:  home venue value
    :param home_value:  value representing home
    :param away_value:  value representing away
    :return:
    """
    return choose_by_eq(HOME_VENUE, home_venue, home_value, away_value)


def local_datetime(dt: datetime):
    """
    Convert a datetime to the local timezone.
    :param dt: datetime to convert
    :return:
    """
    date_time = datetime.now() if dt is None else \
        parse(dt) if isinstance(dt, str) else dt
    return date_time.astimezone(tz=tz.gettz())

