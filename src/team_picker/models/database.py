import logging
import os
import urllib.parse

from flask import Flask
from flask_migrate import Migrate

from .JsonDeEncoder import JsonEncoder, JsonDecoder
from .db_session import db
from .models import add_pre_configured
from ..constants import *
from ..util import logger, is_enabled_for


def make_connection_uri(app: Flask, config: dict) -> str:
    """
    Make a database connection URI.
    See https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/#connection-uri-format.
    :param app:     Flask application
    :param config:  configuration
    :return: uri string
    """
    # dialect+driver://username:password@host:port/database
    cfg = {DB_DIALECT: config[DB_DIALECT].lower()}
    for key, prefix in [(DB_DRIVER, "+"), (DB_USERNAME, ""), (DB_PASSWORD, ""),
                        (DB_HOST, ""), (DB_PORT, ":"),
                        (DB_DATABASE, "")]:
        cfg[key] = config.get(key, None)
        cfg[key] = f'{prefix}{cfg[key]}' if cfg[key] is not None else ''

    if cfg[DB_DIALECT] == 'sqlite':
        # SQLite connects to file-based databases, using the Python
        # built-in module sqlite3 by default.
        for key in [DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT]:
            cfg[key] = ''
        inst_rel_config = config.get(DB_INSTANCE_RELATIVE_CONFIG, False)
        if inst_rel_config:
            cfg[DB_DATABASE] = os.path.join(app.instance_path, cfg[DB_DATABASE])
        # else absolute path
    else:
        cfg[DB_PASSWORD] = f':{urllib.parse.quote_plus(cfg[DB_PASSWORD])}'

    at = '@' if len(cfg[DB_USERNAME]) and len(cfg[DB_PASSWORD]) else ''

    database = f'/{cfg[DB_DATABASE]}' if len(f'{cfg[DB_DATABASE]}') else ''
    uri = f'{cfg[DB_DIALECT]}{cfg[DB_DRIVER]}://' \
          f'{cfg[DB_USERNAME]}{cfg[DB_PASSWORD]}{at}' \
          f'{cfg[DB_HOST]}{cfg[DB_PORT]}{database}'

    return uri


def setup_db(app: Flask, config: dict, init: bool = False):
    """
    Initialise the app for the database, binding a flask application and a
    SQLAlchemy service. Additionally sets custom JSON encoder and decoder for
    the application.
    :param app:      Flask application
    :param config:   database configuration
    :param init:     initialise database
    """
    # Database URI precedence is:
    # 1. DB_URI
    # 2. DB_URI_ENV_VAR
    # 3. make uri from DB_DIALECT etc.
    connection_uri = config[DB_URI] or \
        config[DB_URI_ENV_VAR] or \
        make_connection_uri(app, config)

    # SQLAlchemy 1.4.x has removed support for the postgres:// URI scheme,
    # which is used by Heroku Postgres
    # (https://github.com/sqlalchemy/sqlalchemy/issues/6083)
    if connection_uri.startswith("postgres://"):
        connection_uri = connection_uri.replace(
            "postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = connection_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)

    app.json_encoder = JsonEncoder
    app.json_decoder = JsonDecoder

    if is_enabled_for(logging.DEBUG):
        logger().debug(f"Initialised database: {connection_uri}")
    else:
        logger().info(f"Initialised database")

    migrate = Migrate(app, db)

    if init:
        db_drop_and_create_all()


def db_drop_and_create_all():
    """
    Drop the database tables and start fresh.
    """
    db.drop_all()
    db.create_all()

    # pre-populate roles & teams
    add_pre_configured()

    logger().info(f"Database tables recreated")

