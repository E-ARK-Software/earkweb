# Installation based on Docker images

## Table of Contents 

- [Install Docker and Docker Compose on the host system](#install-docker-on-the-host-system)
- [MySQL image](#mysql-image)
- [Build earkweb image](#build-earkweb-image)
- [Run earkweb image](#run-earkweb-image)

## Install Docker and Docker Compose on the host system

On a linux system, follow the instruction to install docker available at:

  https://docs.docker.com/linux/
    
Install docker compose which allows running multi-container Docker applications as described here:

  https://docs.docker.com/compose/
    
In the following it is assumed that docker commands can be executed without "sudo" (see section "Create a docker group" at https://docs.docker.com/v1.5/installation/ubuntulinux/). 

# Build and run using docker compose

Use the startup script `docker-compose-run.sh` or follow the steps below.

1. Change to the earkweb directory:

        cd /path/to/earkweb
    
2. Build the images:

        docker-compose build
        
3. Create a directory where the mysql data is stored on the host system:

        mkdir /tmp/earkweb-mysql-data
    
4. Run a database container named `tmpdb` based on the image `earkdbimg`:

        docker run --name tmpdb -d -p 3306:3306 -v /tmp/earkweb-mysql-data:/var/lib/mysql earkdbimg
    
5. Run the init script in the database container (named `earkdb`) to create required users and databases:

        docker exec tmpdb /init.sh
    
6. Stop the temporary database container again:

        docker stop tmpdb
    
7. Run the docker-compose which will start multiple containers:

        docker-compose up
    
8. Run the following command in container `earkweb_1` to create a user (parameters: <username> <email> <password> <is_superuser>):

        docker exec -it earkweb_1 python /earkweb/util/createuser.py eark user@email eark true
    
9. Open the following URL in a browser and login with the user created in the previous step:

    http://127.0.0.1:8000
    
To delete data, images and containers created by these steps run the following commands:
 
         docker-compose down
         sudo rm -rf /tmp/earkweb-mysql-data; docker rm tmpdb; docker rmi earkwebimg earkdbimg earkweb_worker;

# Build and run images individually

The earkweb image is build using the main Dockerfile located in the root of the earkweb folder. However, the application depends on multiple other containers. The dependency
between the containers is specified in the `docker-compose.yml` file. The required images are:

* [tutum/mysql](https://hub.docker.com/r/tutum/rabbitmq/)
* [solr](https://hub.docker.com/_/solr/)
* [tutum/rabbitmq](https://hub.docker.com/r/tutum/rabbitmq/)

The mysql image is build using another Dockerfile located in `earkweb/docker/earkdb/Dockerfile` which allows initializing the database. However, the database can also initialized
manuall following the instructions in the [manual installation](./docs/install_manual.md) documentation. 

## MySQL image

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
        
## earkweb image

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
        
