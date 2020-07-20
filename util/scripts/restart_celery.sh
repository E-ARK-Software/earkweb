#!/bin/bash
celery -A earkweb.celery control shutdown
sleep 3
#celery multi start ingestqueue -A earkweb.celery -Ofair --pidfile=/tmp/default_worker.pid --logfile=/tmp/default_worker.log
celery -A earkweb.celery worker --pool threads -Ofair --pidfile=/tmp/default_worker.pid --logfile=/tmp/default_worker.log
sleep 3
celery -A earkweb.celery flower --address=127.0.0.1 --port=5555 --broker=amqp://guest:guest@localhost:5672
