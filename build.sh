# Render.com build script
set -o errexit
pip install -r requirements.txt
flask db upgrade