# Ensure database is upgraded if necessary.
release: flask db upgrade
# Run app
web: gunicorn 'src.team_picker:create_app({})'
# Run app and initialise database
# Must have only one worker, as gunicorn has no inter-worker method of communication to coordinate
# the database initialisation.
# web: gunicorn 'src.team_picker:create_app({"initdb":True})' --workers 1
# Run app
# web: gunicorn 'src.team_picker:create_app({"postman_test":True})'
