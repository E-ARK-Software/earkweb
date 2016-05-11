#!/bin/bash

sleep 5

# Apply database migrations
echo "Apply database migrations"
python /earkweb/manage.py makemigrations
python /earkweb/manage.py migrate
# Start server
echo "Starting server"
python /earkweb/manage.py runserver 0.0.0.0:8000
# Scan tasks
#echo "Scan tasks"
#python /earkweb/workers/scantasks.py