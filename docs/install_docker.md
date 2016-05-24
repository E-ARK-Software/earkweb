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
      
## Install and run using Docker Compose

### Install Docker and Docker Compose on the host system

On a linux system, follow the instruction to install docker available at:

  https://docs.docker.com/linux/
    
Install docker compose which allows running multi-container Docker applications as described here:

  https://docs.docker.com/compose/
    
In the following it is assumed that docker commands can be executed without "sudo" (see section "Create a docker group"
at https://docs.docker.com/v1.5/installation/ubuntulinux/).

### Build and run using docker compose

Use the script `docker-compose-run.sh` or execute the commands described below.

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
        
