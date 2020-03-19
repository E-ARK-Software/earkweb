#!/bin/sh
while ! docker exec tmpdb mysqladmin -u admin -peark ping --silent; do
    echo "waiting ..."
    sleep 1
done
echo "done"
