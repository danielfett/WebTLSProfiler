#!/bin/bash

celery -A wwwtlsprofiler worker --concurrency=2 -l info &
gunicorn -b 0.0.0.0:8000 --access-logfile - wwwtlsprofiler.wsgi
