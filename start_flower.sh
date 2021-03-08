#!/bin/bash
echo "Starting flower ..."
celery -A earkweb.celery flower --url_prefix=flower --port=5555
