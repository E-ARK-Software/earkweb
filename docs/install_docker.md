# Build and run using Docker-Compose

## Configure 

The configuration file `settings/settings.cfg.docker` is used for the docker deployment.

Note that this file is copied to the docker container as the settings file:
    
    earkweb1:/earkweb/settings/settings.cfg

## Build

Bild the docker containers from source: 

    docker-compose build --build-arg USER=$USER db redis rabbitmq solr earkweb celery flower

## Run

Start the docker containers:

    docker-compose up
    
Open the web page:

    http://localhost:8000
    
Stop the containers:

    docker-compose stop
    
Start containers:

    docker-compose start
    
Remove containers:

    docker-compose down
