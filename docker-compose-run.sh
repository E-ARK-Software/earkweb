#!/usr/bin/env bash
file="./config/settings.cfg"
if [ ! -f "$file" ]
  then
  echo "Docker configuration file does not exist. Rename sample config file config/settings.cfg.docker to config/settings.cfg."
  exit 1

fi
line=$(head -n 1 config/settings.cfg)
if [ $line != "#docker-config" ]
  then
  echo "Docker configuration file required (first line #docker-config). Sample config file: config/settings.cfg.docker"
  exit 1
fi

MYSQL_DATA_DIRECTORY="/tmp/earkweb-mysql-data"

REPO_DATA_DIRECTORY="/tmp/earkwebdata"
mkdir -p $REPO_DATA_DIRECTORY

echo "Building the images ..."
docker-compose build

echo "Running mysql database ..."
mkdir $MYSQL_DATA_DIRECTORY
docker run --name tmpdb -d -p 3306:3306 -v /tmp/earkweb-mysql-data:/var/lib/mysql earkdbimg &

DB_PAUSE=20 # the lazy way - could check port 3306 until service becomes available
echo "Pause $DB_PAUSE seconds ..."
sleep $DB_PAUSE

echo "Starting intermediate database container to initialize data directory ..."
docker exec tmpdb /init.sh

echo "Stopping and removing intermediate database container ..."
docker stop tmpdb
docker rm tmpdb

echo "Starting services (docker-compose up) ..."
docker-compose up &

SERVICES_PAUSE=30 # the lazy way - could check until services becomes available
echo "Pause $SERVICES_PAUSE seconds ..."
sleep $SERVICES_PAUSE

echo "Creating user ..."
docker exec -it earkweb_1 python /earkweb/util/createuser.py eark user@email eark true

echo "Scanning tasks ..."
docker exec -it earkweb_1 python /earkweb/workers/scantasks.py

echo "Creating solr core for storage area ..."
docker exec -it --user=solr solr_1 bin/solr create_core -c earkstorage

curl http://localhost:8983/solr/earkstorage/schema -X POST -H 'Content-type:application/json' --data-binary '{    "add-field" : {
        "name":"content",
        "type":"text_general",
        "stored":true,
"indexed": true
    }
}'

curl -X POST -H 'Content-type:application/json' --data-binary '{
    "add-copy-field":{
        "source":"_text_", "dest":[ "content" ]
    }
}' http://localhost:8983/solr/earkstorage/schema

echo "Creating repository directories and files ..."
mkdir $REPO_DATA_DIRECTORY/reception
mkdir $REPO_DATA_DIRECTORY/storage
mkdir $REPO_DATA_DIRECTORY/storage/pairtree_root
touch $REPO_DATA_DIRECTORY/storage/pairtree_version0_1
mkdir $REPO_DATA_DIRECTORY/work
mkdir $REPO_DATA_DIRECTORY/access

mkdir $REPO_DATA_DIRECTORY/nlp
mkdir $REPO_DATA_DIRECTORY/nlp/stanford
mkdir $REPO_DATA_DIRECTORY/nlp/stanford/classifiers
mkdir -p $REPO_DATA_DIRECTORY/nlp/textcategories/models


