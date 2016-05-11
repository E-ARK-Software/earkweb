#!/usr/bin/env bash

docker-compose build

mkdir /tmp/earkweb-mysql-data

docker run --name tmpdb -d -p 3306:3306 -v /tmp/earkweb-mysql-data:/var/lib/mysql earkdbimg &

sleep 7

docker exec tmpdb /init.sh

docker stop tmpdb

docker-compose up &

sleep 7

docker exec -it earkweb_1 python /earkweb/util/createuser.py eark user@email eark