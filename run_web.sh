#!/bin/bash

echo "Waiting for database to start up ..."
#sleep 5
./earkweb/docker/wait-for-it/wait-for-it.sh db:3306

# Apply database migrations
echo "Apply database migrations"
cd /earkweb && python manage.py makemigrations
cd /earkweb && python manage.py migrate
# Start server
echo "Starting server"
cd /earkweb && python manage.py runserver 0.0.0.0:8000