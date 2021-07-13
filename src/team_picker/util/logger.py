import logging
from typing import Union

from flask import Flask

_APP = None
DEFAULT_LOG_LEVEL = 'INFO'


def set_logger(app: Flask, level: Union[int, str] = DEFAULT_LOG_LEVEL):
    """
    Set the application logger
    :param app: Flask app
    :param level: one of 'CRITICAL', 'FATAL', 'ERROR', 'WARN', 'WARNING',
                  'INFO' or 'DEBUG'
    """
    global _APP
    _APP = app
    set_level(level)


def logger(app: Flask = None) -> logging.Logger:
    """
    Get application logger.
    :return:
    """
    if _APP is None and app is not None:
        set_logger(app)
    return _APP.logger


def set_level(level: Union[int, str] = DEFAULT_LOG_LEVEL):
    """
    Set the logger level
    :param level: one of 'CRITICAL', 'FATAL', 'ERROR', 'WARN', 'WARNING',
                  'INFO' or 'DEBUG'
    """
    logger().setLevel(level.upper() if isinstance(level, str) else level)


def is_enabled_for(level: int) -> bool:
    """
    Check if logger is enabled for the specified level.
    :param level: level to check; one of logging.CRITICAL etc.
    :return:
    """
    return logger().isEnabledFor(level)

