#!/bin/sh
python3 manage.py migrate &
redis-server &
celery -A wwwtlsprofiler worker --autoscale=10,0 -l info &
gunicorn -b 0.0.0.0:8000 --access-logfile - wwwtlsprofiler.wsgi
