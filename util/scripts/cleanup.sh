#!/bin/bash

MYSQL_USERNAME=repo
MYSQL_PASSWORD=repo

repo_data_directory="/var/data/earkweb"

echo "Do you want to delete repository data? (y/n, default: n)"
read actiondata
actiondata_val=${actiondata:-n}
if [[ "$actiondata_val" = "y" ]]; then
    if [ ! -z "$repo_data_directory" -a "$repo_data_directory" != " " ]; then
	echo "Deleting repository data"
	rm -rf $repo_data_directory/work/*
	rm -rf $repo_data_directory/storage/pairtree_root/*
	rm -rf $repo_data_directory/reception/*
    fi
fi

echo "Do you want to delete database data? (y/n, default: n)"
read actiondata
actiondata_val=${actiondata:-n}
if [[ "$actiondata_val" = "y" ]]; then
	echo "Deleting database data"
	echo "delete from informationpackage;" | mysql -u $MYSQL_USERNAME -p$MYSQL_PASSWORD earkweb
	echo "delete from search_aip;" | mysql -u $MYSQL_USERNAME -p$MYSQL_PASSWORD earkweb
	echo "delete from search_dip;" | mysql -u $MYSQL_USERNAME -p$MYSQL_PASSWORD earkweb
	echo "delete from search_inclusion;" | mysql -u $MYSQL_USERNAME -p$MYSQL_PASSWORD earkweb
fi

echo "Do you want to reset the index? (y/n, default: y)"
read actiondata
actiondata_val=${actiondata:-y}
if [[ "$actiondata_val" = "y" ]]; then
	echo "Reset solr index: storagecore1"
	curl -X GET "http://localhost:8983/solr/storagecore1/update?stream.body=%3Cdelete%3E%3Cquery%3E*%3C/query%3E%3C/delete%3E&commit=true"
fi

