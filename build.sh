# Render.com build script
set -o errexit
pip install -r requirements.txt
echo -e "app: $FLASK_APP \npython path: $PythonPath"
flask db upgrade