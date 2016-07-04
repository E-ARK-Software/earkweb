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

INITIALIZE=true

MYSQL_DATA_DIRECTORY="/tmp/earkweb-mysql-data"

REPO_DATA_DIRECTORY="/tmp/earkwebdata"

if [ ! -e "$REPO_DATA_DIRECTORY" ];
    then
        echo "Creating new repo directory: $REPO_DATA_DIRECTORY"
        mkdir -p $REPO_DATA_DIRECTORY
    else
        echo "Repo directory already exists: $REPO_DATA_DIRECTORY"
fi

echo "Building the images ..."
docker-compose build

if [ ! -e "$MYSQL_DATA_DIRECTORY" ];
    then
        echo "MySQL data directory does not exist. Creating new data directory at: $MYSQL_DATA_DIRECTORY"
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
    else
        echo "MySQL data directory found at: $MYSQL_DATA_DIRECTORY"
        echo "Checking tables ..."
        DATATABLES=( auth_group auth_group_permissions auth_permission auth_user_groups auth_user auth_user_user_permissions celery_taskmeta celery_tasksetmeta \
            config_path django_admin_log django_content_type django_migrations django_session djcelery_crontabschedule djcelery_crontabschedule djcelery_intervalschedule \
            djcelery_periodictask djcelery_periodictasks djcelery_taskstate djcelery_workerstate earkcore_informationpackage search_aip search_dip search_inclusion \
            sip2aip_mymodel wirings workflow_workflowmodules)
        for DATATABLE in "${DATATABLES[@]}"
        do
            sudo myisamchk -r -q "$MYSQL_DATA_DIRECTORY/eark/$DATATABLE"
        done
        INITIALIZE=false
fi

echo "Starting services (docker-compose up) ..."
docker-compose up &

SERVICES_PAUSE=30 # the lazy way - could check until services becomes available
echo "Pause $SERVICES_PAUSE seconds ..."
sleep $SERVICES_PAUSE

if [ "$INITIALIZE" = true ] ; then
    echo "Creating user ..."
    docker exec -it earkweb_1 python /earkweb/util/createuser.py eark user@email eark true
fi

echo "Scanning tasks ..."
docker exec -it earkweb_1 python /earkweb/workers/scantasks.py

if [ "$INITIALIZE" = true ] ; then
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
fi



