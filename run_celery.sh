#!/bin/sh
echo "Delay to give rabbitmq time to start up"
sleep 10
cd earkweb && celery --app=earkweb.celeryapp:app worker