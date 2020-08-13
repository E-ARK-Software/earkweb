#!/bin/bash
echo "Starting flower ..."
cd /earkweb && celery -A earkweb.celery flower --url_prefix=flower --port=5555 >/var/data/flower.log 2>&1 &
