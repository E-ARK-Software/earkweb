#!/usr/bin/env bash

MYSQL_DATA_DIRECTORY = "/tmp/earkweb-mysql-data"

echo "Building the images ..."
docker-compose build

echo "Runing mysql database ..."
mkdir $MYSQL_DATA_DIRECTORY
docker run --name tmpdb -d -p 3306:3306 -v /tmp/earkweb-mysql-data:/var/lib/mysql earkdbimg &

DB_PAUSE=15 # the lazy way - could check port 3306 until service becomes available
echo "Pause $DB_PAUSE seconds ..."
sleep $DB_PAUSE

echo "Initialising database container ..."
docker exec tmpdb /init.sh

echo "Stopping database container ..."
docker stop tmpdb

echo "Starting services (docker-compose up) ..."
docker-compose up &

SERVICES_PAUSE=30 # the lazy way - could check until services becomes available
echo "Pause $SERVICES_PAUSE seconds ..."
sleep $SERVICES_PAUSE

echo "Creating user ..."
docker exec -it earkweb_1 python /earkweb/util/createuser.py eark user@email eark true

echo "Scan tasks ..."
docker exec -it earkweb_1 python /earkweb/workers/scantasks.py

#echo "Creating solr core for storage area ..."
#docker exec -it --user=solr solr_1 bin/solr create_core -c earkstorage