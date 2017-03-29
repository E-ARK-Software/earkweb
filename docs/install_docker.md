# Installing using Docker

The following installation procedure describes two different ways to install earkweb using docker. The recommended
approach is to use docker-compose which automates the creation of images and handles the dependencies between multiple
running containers for the earkweb frontend, database, solr search, message queue, and task execution backend.
Alternatively, the images can be created using docker individually and configured accordingly.

## Table of Contents 

  - [Install and run using Docker Compose](#install-and-run-using-docker-compose)
    - [Install Docker and Docker Compose on the host system](#install-docker-and-docker-compose-on-the-host-system)
    - [Build and run using docker compose](#build-and-run-using-docker-compose)
  - [Build images and run as individual containers](#build-images-and-run-as-individual-containers)
    - [Install Docker on the host system](#install-docker-on-the-host-system)
    - [Build and run images individually](#build-and-run-images-individually)
      - [MySQL image](#mysql-image)
      - [earkweb image](#earkweb-image)
   - [Troubleshooting](#troubleshooting)
      
## Install and run using Docker Compose

### Install Docker and Docker Compose on the host system

Follow the instruction to install docker available at:

  https://docs.docker.com/engine/installation
    
Install docker compose which allows running multi-container Docker applications as described here:

  https://docs.docker.com/compose/
    
In the following it is assumed that docker commands can be executed without "sudo" (see section "Manage Docker as a non-root user"
at https://docs.docker.com/engine/installation/linux/linux-postinstall/#manage-docker-as-a-non-root-user).

### Execute using docker compose

The script `docker-compose-run.sh` available in the earkweb root directory can be used to build and initialise the images and to run the multi-container application for the first 
time. The script will create a temporary container to initialise the MySQL database, pull the container images from docker hub, start the services, and finally perform some basic
configuration operations.

Execute the following bash script:

    ./docker-compose-run.sh
        
This will initialize the containers needed to run the multi-container application.

Stop the containers by pressing Ctrl+C in the shell where the services were started or execute:

    docker-compose stop -t 120
    
The 2 minutes timeout (-t 120) is to give the services enough time to exit gracefully (default: 10 seconds). After the timeout limit is exceeded, the corresponding processes will be killed.

The second time, to start the earkweb services again it suffices to execute:

    docker-compose start
    
Stopping the database container can lead to MySQL tables being "marked as crashed", see section [MySQL Data tables crashed](#mysql-data-tables-crashed).

#### Build container images

Alternatively, it is possible to build the docker containers from source. Change

    docker-compose build
    
to

    docker-compose pull

in the `./docker-compose-run.sh` script to build the images instead of pulling them from the repository.

#### Execute docker-compose commands indiviually 
 
the steps in the docker-compose shell script can be executed individually as described below.

1. Change to the earkweb directory:

        cd /path/to/earkweb
    
2. Build the images:

        docker-compose build
        
3. Create directories where data will be stored on the host system:

    3.1 MySQL datadirectory

        mkdir /tmp/earkweb-mysql-data

    3.2 Repository data directory

        mkdir /tmp/earkwebdata
    
4. Run an intermediate database container named `tmpdb` based on the image `earkdbimg`:

        docker run --name tmpdb -d -p 3306:3306 -v /tmp/earkweb-mysql-data:/var/lib/mysql earkdbimg
    
5. Run the init script in the database container (named `earkdb`) to create required users and databases:

        docker exec tmpdb /init.sh
    
6. Stop the intermediate database container and remove it:

        docker stop tmpdb
        docker rm tmpdb
    
7. Run the docker-compose which will start multiple containers (this can take a while):

        docker-compose up
    
8. Run the following command in container `earkweb_1` to create a user (parameters: <username> <email> <password> <is_superuser>):

        docker exec -it earkweb_1 python /earkweb/util/createuser.py eark user@email eark true

9. Execute the script for registering tasks:

        docker exec -it earkweb_1 python /earkweb/workers/scantasks.py

10. Create a SolR core for the storage area:

        docker exec -it --user=solr solr_1 bin/solr create_core -c earkstorage

11. Create subdirectories in the repository storage area:

        mkdir /tmp/earkwebdata/{reception, storage, work, access}
    
11. Open the following URL in a browser and login with the user data provided previously:

    http://127.0.0.1:8000
    
To stop the application run:

    docker-compose down

To delete data, images and containers again, run the following commands:

    docker rmi earkweb_celery earkwebimg earkdbimg
    sudo rm -rf /tmp/earkwebdata
    sudo rm -rf /tmp/earkweb-mysql-data/

## Build images and run as individual containers

### Install Docker on the host system

On a linux system, follow the instruction to install docker available at:

  https://docs.docker.com/linux/
    
In the following it is assumed that docker commands can be executed without "sudo" (see section "Create a docker group" at https://docs.docker.com/v1.5/installation/ubuntulinux/). 

### Build and run images individually

The earkweb image is build using the main Dockerfile located in the root of the earkweb folder. However, the application depends on multiple other containers. The dependency
between the containers is specified in the `docker-compose.yml` file.

The earkweb deployment is based on the following images:

* [ubuntu:14.04.5](https://hub.docker.com/_/ubuntu/)
* [tutum/mysql](https://hub.docker.com/r/tutum/rabbitmq/)
* [tutum/rabbitmq](https://hub.docker.com/r/tutum/rabbitmq/)
* [tutum/redis](https://hub.docker.com/r/tutum/redis/)
* [solr](https://hub.docker.com/_/solr/)

Most of these images are provided by "tutum" which is now part of Docker Cloud.

The mysql image is built using another Dockerfile located in `earkweb/docker/earkdb/Dockerfile` which allows initializing the database. However, the database can also initialized
manuall following the instructions in the [manual installation](./docs/install_manual.md) documentation. 

#### MySQL image

1. Change to the earkweb directory:

        cd /path/to/earkweb

2. Build image (the Dockerfile is located in 'earkdb'):

        docker build --tag earkdbimg ./docker/earkdb
        
3. Create a directory where the mysql data is stored on the host system:

        mkdir /tmp/earkweb-mysql-data
    
4. Run mysql container:
    
        docker run --name earkdb -d -p 3306:3306 -v /tmp/earkweb-mysql-data:/var/lib/mysql earkdbimg
        
5. Run the init script in the database container (named `earkdb`) to create required users and databases:

        docker exec earkdb /init.sh
    
5. Get a bash into the container
    
        docker exec -it earkdb bash
    
6. Type `mysql` to get a mysql client:

        root@<container-id>:/# mysql -u root
        Welcome to the MySQL monitor.  Commands end with ; or \g.
        Your MySQL connection id is 9
        Server version: 5.5.47-0ubuntu0.14.04.1 (Ubuntu)
        mysql> show databases;
        +--------------------+
        | Database           |
        +--------------------+
        | information_schema |
        | celerydb           |
        | eark               |
        | mysql              |
        | performance_schema |
        +--------------------+
        5 rows in set (0.00 sec)

        
#### earkweb image

Note that mysql must be running and initialized with the required databases (see previous section [MySQL image](#mysql-image)).

1. Change to the earkweb directory:

        cd /path/to/earkweb

2. Build *earkweb* image using the main `Dockerfile`:

        docker build --tag earkwebimg .
        
3. Use the command `docker inspect earkdb` to get the IP of the database container and adapt the settings in `config/settings.cfg` and `earkweb/settings.py` accordingly.

4. Run earkweb using the *earkweb* directory of the host system as application directory in the container (specified with the parameter -v):

        docker run --name earkweb -v `pwd`:/earkweb -i -t -p 8000:8000 earkwebimg /earkweb/run_web.sh
        
5. Run the following command template to create a user (<username> <email> <password> <is_superuser>):

        docker exec -it earkweb python /earkweb/util/createuser.py eark user@email eark true
        
6. Open the following URL in your browser and login with the user data provided in the previous step:

        http://127.0.0.1:8000
        
## Troubleshooting

## MySQL Data tables crashed

According to the docker-compose documentation (https://docs.docker.com/compose/faq/) there is a timeout when stopping containers:

    "Compose stop attempts to stop a container by sending a SIGTERM. It then waits for a default timeout of 10 seconds. After the timeout, a SIGKILL is sent to the container to 
    forcefully kill it. If you are waiting for this timeout, it means that your containers aren’t shutting down when they receive the SIGTERM signal."

If the MySQL container was killed, the tables can be "marked as crashed":

    Table './mydb/mytable' is marked as crashed and should be repaired
    
In this case, while the database container (named 'earkdb_1' by default) is running, execute the following command to repair the tables:

    docker exec -it --user=root earkdb_1 /repair_tables.sh
    
The `repair_tables.sh` shell script is available at `earkweb/docker/earkdb/repair_tables.sh`.

## `ERROR: driver failed programming external connectivity on endpoint [...]`

_You should know what you are doing here to avoid unwanted side effects._ It is currently unclear why this happens,
but it occurs after updating the docker containers/images, most likely because services/containers are not shut
down properly.

This error is tied to local services listening on specific ports. Those processes can be identified through:

    sudo netstat -peanut | grep ":8000"
    
Subsitute `:8000` with the port in the error message. The last output column is `PID/Program name`. Either stop 
the service with `sudo service <servicename> stop` or kill the process with `kill -9 <PID>`. 

_Known error ports and their services:_

* `0.0.0.0:3306` is a mysql service. Use `sudo service mysql stop`.
* `0.0.0.0:15672` is probably related to RabbitMQ. Use `kill -9 <PID>`.
