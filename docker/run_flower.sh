#!/bin/bash
echo "Starting flower ..."
cd /earkweb && celery -A earkweb.celery flower --url_prefix=flower --port=5555
