# Ensure database is upgraded if necessary.
release: flask db upgrade
# Run app
web: gunicorn 'src.team_picker:create_app({})'
