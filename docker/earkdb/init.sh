#!/bin/bash
# initialize

mysql -uroot -e "CREATE DATABASE IF NOT EXISTS eark;"
mysql -uroot -e "GRANT ALL ON eark.* TO arkiv@'%' IDENTIFIED BY 'arkiv';"
mysql -uroot -e "CREATE DATABASE IF NOT EXISTS celerydb;"
mysql -uroot -e "GRANT ALL ON celerydb.* TO arkiv@'%' IDENTIFIED BY 'arkiv';"
