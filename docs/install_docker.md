# Installation based on Docker images

## Table of Contents 

- [Install docker on the host system](#install-docker-on-the-host-system)
- [MySQL image](#mysql-image)
- [Build earkweb image](#build-earkweb-image)
- [Run earkweb image](#run-earkweb-image)

## Install docker on the host system

On a linux system, follow the instruction to install docker available at:

    https://docs.docker.com/linux/
    
In the following it is assumed that docker commands can be executed without "sudo" (see section "Create a docker group" at https://docs.docker.com/v1.5/installation/ubuntulinux/). 

## MySQL image

1. Download and run mysql image

        docker pull tutum/mysql

2. Create data directory with the corresponding read/write permissions on the host system:

        sudo mkdir -p /var/data/docker-mysql
        sudo chown <user>:<user> /var/data/docker-mysql
       
3. Run mysql docker image:

        docker run -d -p 3306:3306 -v /var/data/docker-mysql:/var/lib/mysql tutum/mysql
        
4. Login to mysql container, create databases and user and set permissions in mysql (login with empty password for 'root'):

        docker exec -it <mysql-container-id> bash
        
        root@<mysql-container-id>:/# mysql -u root -p
        Enter password: <leave empty>
        
        mysql> create database eark;
        mysql> CREATE USER 'arkiv'@'%' IDENTIFIED BY 'arkiv';
        mysql> GRANT ALL ON eark.* TO arkiv@'%' IDENTIFIED BY 'arkiv';
        mysql> create database celerydb;
        mysql> GRANT ALL ON celerydb.* TO arkiv@'%' IDENTIFIED BY 'arkiv';
        
## Build earkweb image

5. The Dockerfile to build the *earkweb* image is located in the *earkweb* root directory:

        cd /path/to/earkweb
        cat ./Dockerfile

6. Build *earkweb* docker image:

        docker build .
        
7. Tag the image created:

        docker tag <image-id> earkweb
        
## Run earkweb image
        
8. Run earkweb:

        docker run -i -t -p 8000:8000 earkweb python /earkweb/manage.py runserver 0.0.0.0:8000 
        
8. Open the following URL in your browser:

        http://127.0.0.1:8000
        
