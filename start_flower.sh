#!/bin/bash
echo "Starting flower ..."
source ./venv/bin/activate
celery -A earkweb.celery flower --url_prefix=flower --port=5555
