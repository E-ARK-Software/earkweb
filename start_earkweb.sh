#!/bin/bash
echo "Starting earkweb ..."
source ./venv/bin/activate
uwsgi --ini earkweb.ini
