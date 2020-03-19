#!/bin/bash
# initialize

mysql -uroot -e "CREATE DATABASE IF NOT EXISTS earkdb;"
mysql -uroot -e "GRANT ALL ON earkdb.* TO eark@'%' IDENTIFIED BY 'eark';"