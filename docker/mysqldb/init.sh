#!/bin/bash
# initialize

mysql -uroot -e "CREATE DATABASE IF NOT EXISTS repodb;"
mysql -uroot -e "GRANT ALL ON repodb.* TO repo@'%' IDENTIFIED BY 'repo';"