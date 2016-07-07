#!/bin/bash
file="./config/settings.cfg"
if [ ! -f "$file" ]
  then
  echo "Configuration file does not exist. Rename sample config file config/settings.cfg.docker to config/settings.cfg."
  exit 1
fi
line=$(head -n 1 config/settings.cfg)
if [ $line != "#docker-config" ]
  then
  echo "Docker configuration file required (first line #docker-config). Sample config file: config/settings.cfg.docker"
  exit 1
fi
function get_config_val()
{
    local  config_val=`cat $file | grep "$1" | sed "s/"$1"\s\{0,\}=\s\{0,\}//g"`
    echo "$config_val"
}

echo "Stopping containers ..."
docker-compose stop

docker_mysql_data_directory=$(get_config_val "docker_mysql_data_directory")
docker_repo_data_directory=$(get_config_val "docker_repo_data_directory")
echo "Docker mysql data directory: $docker_mysql_data_directory"
echo "Docker repository data directory: $docker_repo_data_directory"
echo "Do you want to delete these data directories? (y/n, default: y)"
read actiondata
actiondata_val=${actiondata:-y}
if [[ "$actiondata_val" = "y" ]]; then
    if [ ! -z "$docker_mysql_data_directory" -a "$docker_mysql_data_directory" != " " ]; then
        sudo rm -rf $docker_mysql_data_directory
    fi
    if [ ! -z "$docker_repo_data_directory" -a "$docker_repo_data_directory" != " " ]; then
        sudo rm -rf $docker_repo_data_directory
    fi
fi

echo "Delete ALL containers from Docker which were executed previously."
echo "Do you want to delete all containers from Docker? (y/n, default: y)"
read actionct
actionct_val=${actionct:-y}
if [[ "$actionct_val" = "y" ]]; then
   docker rm $(docker ps -aq)
fi

echo "Delete earkweb images. Note that rebuilding images takes time."
echo "Delete images? (y/n, default: n)"
read actionimg
actionimg_val=${actionimg:-n}
if [[ "$actionimg_val" = "y" ]]; then
   docker rm tmpdb; docker rmi earkwebimg earkdbimg earkweb_celery;
fi

