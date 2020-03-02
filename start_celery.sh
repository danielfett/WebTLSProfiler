#!/bin/bash

export PYTHONPATH=$PYTHONPATH:~/Documents/yes/tlsprofiler:~/Documents/yes/sslyze:~/Documents/yes/nassl

 celery -A wwwtlsprofiler worker --concurrency=2 -l info
