#!/bin/bash
echo "Starting celery ..."
# cd /earkweb && celery multi start ingestqueue -A earkweb.celery --concurrency=4 -Ofair --pidfile=/data/celery_worker.pid  --logfile=/data/celery_default_queue.log
# cd /earkweb && celery -A earkweb.celery worker --pool threads -Ofair --pidfile=/data/celery_worker.pid  --logfile=/data/celery_default_queue.log &
source ./.venv/bin/activate
celery -A earkweb.celery worker --pool prefork -Ofair  --loglevel=debug
