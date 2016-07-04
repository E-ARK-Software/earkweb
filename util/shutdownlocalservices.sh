#!/usr/bin/env bash
echo "start/stop/status?"
read action
services=(mysql rabbitmq-server redis-server)
for service in ${services[@]}; do sudo service $service $action; done