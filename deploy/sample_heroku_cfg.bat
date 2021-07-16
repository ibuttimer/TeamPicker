set APP_NAME=your-heroku-app-name

call heroku config:set INST_REL_CONFIG=True --app %APP_NAME%

rem Environment variable equivalents of command line arguments.
rem If set to True, initialise the database on boot
rem call heroku config:set INIT_DB_ARG=True --app %APP_NAME%
rem If set to True, disable server-side sessions
rem call heroku config:set POSTMAN_TEST_ARG=True --app %APP_NAME%
rem If set, generate API documentation
rem call heroku config:set GENERATE_API_ARG=api.md --app %APP_NAME%

rem Log level can be one of 'CRITICAL', 'FATAL', 'ERROR', 'WARN', 'WARNING', 'INFO' or 'DEBUG'
call heroku config:set LOG_LEVEL=DEBUG --app %APP_NAME%

call heroku config:set SECRET_KEY="`< /dev/urandom tr -dc 'a-zA-Z0-9' | head -c16`" --app %APP_NAME%
call heroku config:set DEBUG=True --app %APP_NAME%
call heroku config:set TESTING=False --app %APP_NAME%

rem Database URI, if specified (i.e. not None) it is used, otherwise the
rem DB_URI_ENV_VAR or DB_DIALECT etc. variables are used to construct the
rem Database URL
call heroku config:set DB_URI=None --app %APP_NAME%

rem Database URI environment variable, if specified (i.e. not None) it is used,
rem otherwise the DB_URI or DB_DIALECT etc. variables are used to construct the
rem Database URL
call heroku config:set DB_URI_ENV_VAR=DATABASE_URL --app %APP_NAME%

rem https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/#connection-uri-format
rem See https://docs.sqlalchemy.org/en/14/core/engines.html#supported-databases.
call heroku config:set DB_DIALECT=sqlite --app %APP_NAME%
call heroku config:set DB_DRIVER=None --app %APP_NAME%
call heroku config:set DB_USERNAME=None --app %APP_NAME%
call heroku config:set DB_PASSWORD=None --app %APP_NAME%
call heroku config:set DB_HOST=None --app %APP_NAME%
call heroku config:set DB_PORT=0 --app %APP_NAME%
call heroku config:set DB_DATABASE=teampicker --app %APP_NAME%

rem SQLite specific, if true, database file path will be generated relative to
rem app instance folder, otherwise database file path should be absolute.
call heroku config:set DB_INSTANCE_RELATIVE_CONFIG=True --app %APP_NAME%

rem Example SQLite database settings:
rem Absolute path:
rem   Unix/Mac:   {'DB_DATABASE': '/absolute/path/to/foo.db',
rem                'DB_INSTANCE_RELATIVE_CONFIG': False}
rem   Windows:    {'DB_DATABASE': 'C:\\absolute\\path\\to\\foo.db',
rem                'DB_INSTANCE_RELATIVE_CONFIG': False}
rem App instance folder:
rem   Unix/Mac:   {'DB_DATABASE': 'foo.db', 'DB_INSTANCE_RELATIVE_CONFIG': True}
rem   Windows:    {'DB_DATABASE': 'foo.db', 'DB_INSTANCE_RELATIVE_CONFIG': True}

rem Disable FSADeprecationWarning
call heroku config:set SQLALCHEMY_TRACK_MODIFICATIONS=False --app %APP_NAME%


rem Auth0 authentication related settings:
rem Domain from Application settings in Auth0.
call heroku config:set AUTH0_DOMAIN=your.domain.auth0.com --app %APP_NAME%
rem Signing Algorithm from API settings in Auth0.
call heroku config:set ALGORITHMS=['RS256'] --app %APP_NAME%
rem Identifier from API settings in Auth0.
call heroku config:set AUTH0_AUDIENCE=audience_identifier --app %APP_NAME%

rem Client ID from Application settings in Auth0.
call heroku config:set AUTH0_CLIENT_ID=app_client_id --app %APP_NAME%
rem Client Secret from Application settings in Auth0.
call heroku config:set AUTH0_CLIENT_SECRET=app_client_secret --app %APP_NAME%
rem Allowed Callback URL from Application settings in Auth0.
call heroku config:set AUTH0_CALLBACK_URL=http://your_app/callback --app %APP_NAME%
rem Allowed Logout URL from Application settings in Auth0.
call heroku config:set AUTH0_LOGGED_OUT_URL=http://your_app/ --app %APP_NAME%

rem Client ID from Machine to Machine Application settings in Auth0.
call heroku config:set NON_INTERACTIVE_CLIENT_ID=m2m_app_client_id --app %APP_NAME%
rem Client Secret from Machine to Machine Application settings in Auth0.
call heroku config:set NON_INTERACTIVE_CLIENT_SECRET=m2m_app_client_secret --app %APP_NAME%

rem TeamManager Role ID from Auth0 roles
call heroku config:set TEAM_PLAYER_ROLE_ID=rol_player_id --app %APP_NAME%
rem TeamPlayer Role ID from Auth0 roles
call heroku config:set TEAM_MANAGER_ROLE_ID=rol_manager_id --app %APP_NAME%

rem Server-side session setting
call heroku config:set SESSION_TYPE=sqlalchemy --app %APP_NAME%
call heroku config:set PERMANENT_SESSION_LIFETIME=36000 --app %APP_NAME%

rem Flask run settings
call heroku config:set FLASK_APP=src.team_picker:create_app({}) --app %APP_NAME%
call heroku config:set PYTHONPATH=/app/src --app %APP_NAME%