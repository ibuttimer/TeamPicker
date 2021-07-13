# Ensure database is upgraded if necessary.
release: flask db upgrade
# Run app
# web: gunicorn 'src.team_picker:create_app({})'
# Run app and initialise database
# web: gunicorn 'src.team_picker:create_app({"initdb":True})'
# Run app
web: gunicorn 'src.team_picker:create_app({"postman_test":True})'
