#!/bin/bash

MYSQL_USERNAME=arkiv
MYSQL_PASSWORD=arkiv

# Cleanup woking dir
rm -rf /var/data/earkweb/work/*
rm -rf /var/data/earkweb/storage/pairtree_root/*
# Update status in DB
echo "delete from earkcore_informationpackage;" | mysql -u $MYSQL_USERNAME -p$MYSQL_PASSWORD eark
echo "delete from search_aip;" | mysql -u $MYSQL_USERNAME -p$MYSQL_PASSWORD eark
echo "delete from search_dip;" | mysql -u $MYSQL_USERNAME -p$MYSQL_PASSWORD eark
echo "delete from search_inclusion;" | mysql -u $MYSQL_USERNAME -p$MYSQL_PASSWORD eark

