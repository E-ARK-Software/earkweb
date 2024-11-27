#!/bin/bash
echo "Starting celery beat ..."
source ./venv/bin/activate
celery -A earkweb.celery beat  --loglevel=debug
