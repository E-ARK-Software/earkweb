#!/bin/bash
config_file="settings/settings.cfg"
source scripts/read_config.sh

flower_user=$(get_config_value "$config_file" "server" "flower_user")
flower_password=$(get_config_value "$config_file" "server" "flower_password")

echo "Starting flower ..."
source ./venv/bin/activate
celery -A earkweb.celery flower --basic_auth=${flower_user}:${flower_password} --url_prefix=flower --port=5555