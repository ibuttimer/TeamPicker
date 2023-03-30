# Render.com build script
set -o errexit
pip install -r requirements.txt
echo -e "$FLASK_APP \n$PythonPath"
flask db upgrade