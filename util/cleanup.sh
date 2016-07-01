#!/bin/bash

MYSQL_USERNAME=arkiv
MYSQL_PASSWORD=arkiv

# Cleanup woking dir
rm -rf /var/data/earkweb/work/*
rm -rf /var/data/earkweb/storage/pairtree_root/*
rm -rf /var/data/earkweb/reception/*
# Update status in DB
echo "delete from earkcore_informationpackage;" | mysql -u $MYSQL_USERNAME -p$MYSQL_PASSWORD eark
echo "delete from search_aip;" | mysql -u $MYSQL_USERNAME -p$MYSQL_PASSWORD eark
echo "delete from search_dip;" | mysql -u $MYSQL_USERNAME -p$MYSQL_PASSWORD eark
echo "delete from search_inclusion;" | mysql -u $MYSQL_USERNAME -p$MYSQL_PASSWORD eark

# delete index
curl -X GET "http://localhost:8983/solr/earkstorage/update?stream.body=%3Cdelete%3E%3Cquery%3E*%3C/query%3E%3C/delete%3E&commit=true"
