#!/bin/sh
# source venv/bin/activate

# checks exit code for 'flask db upgrade'. if non-zero, retries
# while true; do
#     flask db upgrade
#     if [[ "$?" == "0" ]]; then
#         break
#     fi
#     echo Upgrade command failed, retrying in 5 secs...
#     sleep 5
# done
flask db upgrade
flask translate compile

# pip install debugpy -t /tmp
# python /tmp/debugpy --wait-for-client --listen 0.0.0.0:5678 -m flask run --host 0.0.0.0 --port 5000
gunicorn flask_blog:app
# exec gunicorn -b :5000 --access-logfile - --error-logfile - flask_blog:app
