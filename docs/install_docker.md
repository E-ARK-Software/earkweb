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

Use the setup script `setup.sh` or follow the steps below.

1. Change to the docker directory in your earkweb copy:

        cd /path/to/earkweb/docker/
    
2. Build the images:

        docker-compose build
        
3. Create a directory which holds the mysql data:

        mkdir /tmp/earkweb-mysql-data
    
4. Run a temporary database container named `tmpdb` based on the image `earkdbimg`:

        docker run --name tmpdb -d -p 3306:3306 -v /tmp/earkweb-mysql-data:/var/lib/mysql earkdbimg
    
5. Run the init script in the database container (named `earkdb`) to create required users and databases:

        docker exec tmpdb /init.sh
    
6. Stop the temporary database container again:

        docker stop tmpdb
    
7. Run the docker-compose which will start multiple containers:

        docker-compose up
    
8. Run the following command in container `earkweb_1` template to create a user (<username> <email> <password>):

        docker exec -it earkweb_1 python /earkweb/util/createuser.py eark user@email eark
    
9. Open the following URL in a browser and login with the user created in the previous step:

    http://127.0.0.1:8000
    
To delete data, images and containers created by these steps run the following commands:
 
         docker-compose down
         sudo rm -rf /tmp/earkweb-mysql-data; docker rm tmpdb earkweb_1 earkdb_1; docker rmi earkwebimg earkdbimg;

# Build and run images individually

## MySQL image

1. Change to docker directory:

        cd /path/to/earkweb/docker/

2. Build image (the Dockerfile is located in 'earkdb'):

        docker build --tag earkdbimg ./earkdb
    
3. Run mysql container:
    
        docker run --name earkdb -d -p 3306:3306 -v `pwd`/earkdb/data:/var/lib/mysql earkdbimg
    
4. Get a bash into the container
    
        docker exec -it earkdb bash
    
5. Type `mysql` to get a mysql client:

        root@<container-id>:/# mysql -u root
        Welcome to the MySQL monitor.  Commands end with ; or \g.
        Your MySQL connection id is 9
        Server version: 5.5.47-0ubuntu0.14.04.1 (Ubuntu)
        mysql> show databases;
        
## earkweb image

1. Change to the *earkweb* directory:

        cd /path/to/earkweb/docker/

2. Build *earkweb* image  (the Dockerfile is located in 'earkweb'):

        docker build --tag earkwebimg ./earkweb
        
3. Use the command `docker inspect earkdb` to get the IP of the database container and adapt the settings in `config/settings.cfg` and `earkweb/settings.py` accordingly.

4. Run earkweb:

        docker run --name earkweb -i -t -p 8000:8000 earkwebimg /docker-entrypoint.sh
        
5. Run the following command template to create a user (<username> <email> <password>):

        docker exec -it earkweb python /earkweb/util/createuser.py eark user@email eark
        
6. Open the following URL in your browser and login with the user data provided in the previous step:

        http://127.0.0.1:8000
        
