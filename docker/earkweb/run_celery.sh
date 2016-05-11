#!/bin/sh

cd earkweb
# run Celery worker
celery --app=earkweb.celeryapp:app worker -Q default -n default
