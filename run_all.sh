#!/bin/bash
echo "Starting celery ..."
cd /earkweb && celery multi start ingestqueue -A earkweb.celery --concurrency=4 -Ofair --pidfile=/data/celery_worker.pid  --logfile=/data/celery_default_queue.log
sleep 3
echo "Starting flower ..."
cd /earkweb && celery -A earkweb.celery flower --port=5555 >/data/flower.log 2>&1 &
sleep 3
echo "Starting earkweb ..."
cd /earkweb && python3 manage.py runserver 0.0.0.0:8000
