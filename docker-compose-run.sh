#!/usr/bin/env bash
HEADER="\e[34m"
OKGREEN="\e[92m"
WARNING="\e[93m"
FAIL="\e[91m"
ENDC="\e[0m"
BOLD="\e[1m"
UNDERLINE="\033[4m"

function echo_highlight()
{
    echo -e "$1$2$ENDC"
}

function echo_highlight_header()
{
    echo -e "$1==========================================================="
    echo -e "$2"
    echo -e "===========================================================$ENDC"
}

file="./config/settings.cfg"
if [ ! -f "$file" ]
  then
  echo_highlight $WARNING "Docker configuration file does not exist. Rename sample config file config/settings.cfg.docker to config/settings.cfg."
  exit 1

fi
line=$(head -n 1 config/settings.cfg)
if [ $line != "#docker-config" ]
  then
  echo_highlight $WARNING "Docker configuration file required (first line #docker-config). Sample config file: config/settings.cfg.docker"
  exit 1
fi
function get_config_val()
{
    local  config_val=`cat $file | grep "$1" | sed "s/"$1"\s\{0,\}=\s\{0,\}//g"`
    echo "$config_val"
}

function exit_if_service_running()
{
    echo_highlight $HEADER "Check if $1 service is running on port $2"
    CHECK_MYSQL=`lsof -u $1 -i :$2`
    if [ -n "$CHECK_MYSQL" ]; then
        echo_highlight $FAIL "A $1 service is running on port $2. Please stop this service first and then re-execute the script."
        exit 1
    fi
}

chmod +x docker/wait-for-it/wait-for-it.sh

INITIALIZE=true

docker_mysql_data_directory=$(get_config_val "docker_mysql_data_directory")
MYSQL_DATA_DIRECTORY="$docker_mysql_data_directory"
docker_repo_data_directory=$(get_config_val "docker_repo_data_directory")
REPO_DATA_DIRECTORY="$docker_repo_data_directory"

echo_highlight_header $HEADER "Repository data directories"

if [ ! -e "$REPO_DATA_DIRECTORY" ];
    then
        echo "Creating new repo directory"
        mkdir -p $REPO_DATA_DIRECTORY
        if [ -e "$REPO_DATA_DIRECTORY" ]
          then
            echo "Creating repository directories and files"
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
            echo_highlight $OKGREEN "Repository data directories created:"
            find $REPO_DATA_DIRECTORY
        fi
    else
        echo "Repo directory already exists: $REPO_DATA_DIRECTORY"
fi

echo_highlight_header $HEADER "Building Docker images"

# change to docker-compose build to build images from source instead of pulling them from the repository
docker-compose pull

exit_if_service_running "rabbitmq" 5672
exit_if_service_running "mysql" 3306
exit_if_service_running "redis" 6379

echo_highlight $HEADER "Creating MySQL image"

if [ ! -e "$MYSQL_DATA_DIRECTORY" ];
    then
        echo "MySQL data directory does not exist. Creating new one."
        echo "Running mysql database ..."
        mkdir $MYSQL_DATA_DIRECTORY
        if [ -e "$MYSQL_DATA_DIRECTORY" ]
          then
            echo_highlight $OKGREEN "MySQL data directory created: $MYSQL_DATA_DIRECTORY"
        fi
        echo "Starting intermediate database container to initialize data directory ..."
        docker run --name tmpdb -d -p 3306:3306 -v /tmp/earkweb-mysql-data:/var/lib/mysql shsdev/earkdb &

        DB_PAUSE=60 # the lazy way - could check port 3306 until service becomes available
        echo "Pause $DB_PAUSE seconds ..."
        sleep $DB_PAUSE
        echo "Waiting for MySQL service to become available"
        ./docker/wait-for-it/wait-for-it.sh $(get_config_val "mysql_server_ip_external"):3306

        echo "Initializing database container ..."
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

echo_highlight_header $HEADER "Starting services (docker-compose up)"

docker-compose up &

SERVICES_PAUSE=60 # the lazy way - could check until services becomes available
echo "Pause $SERVICES_PAUSE seconds ..."
sleep $SERVICES_PAUSE
echo "Waiting for Web UI to become available"
./docker/wait-for-it/wait-for-it.sh $(get_config_val "django_service_ip"):8000

echo_highlight_header $HEADER "Configuring earkweb"

if [ "$INITIALIZE" = true ] ; then
    echo_highlight $HEADER "Creating user"
    docker exec -it earkweb_1 python /earkweb/util/createuser.py eark user@email eark true
    echo_highlight $OKGREEN "User created"
fi

#echo_highlight $HEADER "Scanning tasks (registering task modules in the database)"
#docker exec -it earkweb_1 python /earkweb/workers/scantasks.py

django_service_ip=`cat $file | grep "django_service_ip" | sed 's/django_service_ip\s\{0,\}=\s\{0,\}//g'`

if [ "$INITIALIZE" = true ] ; then
    echo_highlight $HEADER "Creating solr core for storage area"
    docker exec -it --user=solr solr_1 bin/solr create_core -c earkstorage
#    storage_solr_server_ip=$(get_config_val "django_service_ip")

    echo_highlight $HEADER "Running the update script"
    docker exec -it earkweb_1 python earkweb/autoupdate.py
fi

sleep 20

echo_highlight $OKGREEN "Docker deployment ready."


