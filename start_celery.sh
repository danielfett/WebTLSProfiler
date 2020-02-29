#!/bin/bash

export PYTHONPATH=$PYTHONPATH:~/Documents/yes/tlsprofiler:~/Documents/yes/sslyze:~/Documents/yes/nassl

if [ "$1" = "0" ]; then
  celery -A wwwtlsprofiler worker --concurrency=2 -l info
else
  celery -A wwwtlsprofiler beat -l info
fi
