#!/bin/bash

# Note: variables set in the environment, take priority.

# Variables expansion:
# If you use variables in values, ensure they are surrounded with { and }, like ${VAR_TO_EXPAND},
# as bare variables such as VAR_TO_EXPAND are not expanded.

# If set to True, relative filenames for loading the config are assumed to be relative to the instance path
# instead of the application root.
export INST_REL_CONFIG=True

# Environment variable equivalents of command line arguments.
# If set to True, initialise the database on boot
export INIT_DB_ARG=False
# If set to True, disable server-side sessions
export POSTMAN_TEST_ARG=False
# If set, generate API documentation
export GENERATE_API_ARG=None

# Log level can be one of 'CRITICAL', 'FATAL', 'ERROR', 'WARN', 'WARNING', 'INFO' or 'DEBUG'
export LOG_LEVEL=DEBUG

export SECRET_KEY='dev_key'
export DEBUG=True         # Debug mode; True or False.
export TESTING=False      # Testing mode; True or False.

# Database URI, if specified (i.e. not None) it is used, otherwise the
# DB_URI_ENV_VAR or DB_DIALECT etc. variables are used to construct the
# Database URL
export DB_URI=None

# Database URI environment variable, if specified (i.e. not None) it is used,
# otherwise the DB_URI or DB_DIALECT etc. variables are used to construct the
# Database URL
export DB_URI_ENV_VAR=None

# https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/#connection-uri-format
# See https://docs.sqlalchemy.org/en/14/core/engines.html#supported-databases.
export DB_DIALECT=postgresql
export DB_DRIVER=None         # Use default driver.
export DB_USERNAME=postgres
export DB_PASSWORD=password
export DB_HOST=localhost
export DB_PORT=5432
export DB_DATABASE=teampicker

# SQLite specific, if true, database file path will be generated relative to
# app instance folder, otherwise database file path should be absolute.
export DB_INSTANCE_RELATIVE_CONFIG=True

# Example SQLite database settings:
# Absolute path:
#   Unix/Mac:   {'DB_DATABASE': '/absolute/path/to/foo.db',
#                'DB_INSTANCE_RELATIVE_CONFIG': False}
#   Windows:    {'DB_DATABASE': 'C:\\absolute\\path\\to\\foo.db',
#                'DB_INSTANCE_RELATIVE_CONFIG': False}
# App instance folder:
#   Unix/Mac:   {'DB_DATABASE': 'foo.db', 'DB_INSTANCE_RELATIVE_CONFIG': True}
#   Windows:    {'DB_DATABASE': 'foo.db', 'DB_INSTANCE_RELATIVE_CONFIG': True}

export SQLALCHEMY_TRACK_MODIFICATIONS=False  # disable FSADeprecationWarning

# Server-side session type; one of "filesystem" or "sqlalchemy"
export SESSION_TYPE=sqlalchemy
# The lifetime of a permanent session, an integer representing seconds.
export PERMANENT_SESSION_LIFETIME=36000


# Auth0 authentication related settings:
# Domain from Application settings in Auth0.
export AUTH0_DOMAIN=<auth0 domain>
# Signing Algorithm from API settings in Auth0.
export ALGORITHMS=['RS256']
# Identifier from API settings in Auth0.
export AUTH0_AUDIENCE=<auth0 identifier>

# Client ID from Application settings in Auth0.
export AUTH0_CLIENT_ID=<auth0 client id>
# Client Secret from Application settings in Auth0.
export AUTH0_CLIENT_SECRET=<auth0 client secret>
# Application base URL
export BASE_URL=http://localhost:5000/
# Allowed Callback URL from Application settings in Auth0.
export AUTH0_CALLBACK_URL=${BASE_URL}callback
# Allowed Logout URL from Application settings in Auth0.
export AUTH0_LOGGED_OUT_URL=${BASE_URL}

# Client ID from Machine to Machine Application settings in Auth0.
export NON_INTERACTIVE_CLIENT_ID=<auth0 m2m client id>
# Client Secret from Machine to Machine Application settings in Auth0.
export NON_INTERACTIVE_CLIENT_SECRET=<auth0 m2m client secret>

# TeamManager Role ID from Auth0 roles
export TEAM_PLAYER_ROLE_ID=<player role id>
# TeamPlayer Role ID from Auth0 roles
export TEAM_MANAGER_ROLE_ID=<manager role id>

