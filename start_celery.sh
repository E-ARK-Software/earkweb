#!/bin/bash
echo "Starting celery ..."
# cd /earkweb && celery multi start ingestqueue -A earkweb.celery --concurrency=4 -Ofair --pidfile=/data/celery_worker.pid  --logfile=/data/celery_default_queue.log
# cd /earkweb && celery -A earkweb.celery worker --pool threads -Ofair --pidfile=/data/celery_worker.pid  --logfile=/data/celery_default_queue.log &
# time: 1800 => 30 minutes maximum task runtime
source ./venv/bin/activate
celery -A earkweb.celery worker --pool prefork -Ofair  --time-limit=1860 --soft-time-limit=1800 --loglevel=debug
