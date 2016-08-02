# Manual installation

## Table of Contents 

  - [Installing dependencies](#installing-dependencies)
    - [Debian packages](#debian-packages)
    - [Python modules](#python-modules)
      - [fido](#fido)
      - [ghostscript](#ghostscript)
  - [Installing earkweb](#installing-earkweb)
  - [Create and initialize database](#create-and-initialize-database)  
  - [Celery distributed task execution](#celery-distributed-task-execution)

## Installing dependencies

### Install Debian packages

    sudo apt-get install python python-setuptools build-essential python-virtualenv python-dev  summain jhove pdftohtml graphicsmagick imagemagick libgraphicsmagick++1-dev libboost-python-dev

### Python modules

#### fido

[Fido](https://github.com/openpreserve/fido) is used for file format identification (mime-type and PRONOM Unique Identifier).

1. Install fido:

        wget https://github.com/openpreserve/fido/archive/1.3.2-81.tar.gz
        tar -xzvf 1.3.2-81.tar.gz
        cd fido-1.3.2-81
        sudo python setup.py install

2. Update filetype signatures (long running):

        cd fido
        python update_signatures.py

#### ghostscript

1. Install ghostscript (PDF to PDF/A conversion):

    1.1. Download: [Ghostscript 9.18] (http://downloads.ghostscript.com/public/ghostscript-9.18.tar.gz):
    
        wget http://downloads.ghostscript.com/public/old-gs-releases/ghostscript-9.18.tar.gz

    1.2. Installation: [how to install] (http://www.ghostscript.com/doc/9.18/Install.htm):

        tar -xzf ghostscript-9.18.tar.gz
        cd ghostscript-9.18
        ./configure
        make
        sudo make install

## Install message queue and result backend

Install message queue:

    sudo apt-get install rabbitmq-server

Install result backend database:

    sudo apt-get install redis-server

## Install peripleo

### Install postgres

    sudo apt-get install postgresql
    sudo -i -u postgres
    psql
    > psql (9.3.4)
    Type "help" for help.
    postgres=# create database peripleo ;
    CREATE DATABASE
    postgres=# create user peripleo_user ;
    CREATE ROLE
    postgres=# alter user peripleo_user with encrypted password 'arkiv';
    ALTER ROLE
    postgres=# alter database peripleo owner to peripleo_user ;
    ALTER DATABASE
    postgres=# \q
    postgres@eark-pilot:~$ 

### Install peripleo

    cd /srv/
    sudo mkdir pelagios
    sudo chown ${user}:{group} pelagios
    cd pelagios/
    git clone https://github.com/pelagios/peripleo.git
    cd peripleo/lib
    wget http://earkdev.ait.ac.at/eark/pilots/scalagios-core_2.10-2.0.0.jar
    cd /srv/pelagios/peripleo/conf/
    cp application.conf.template application.conf
  
#### Adapt settings in `applicaton.conf`

Comment out the sql driver:

    #db.default.driver="org.sqlite.JDBC"
    #db.default.url="jdbc:sqlite:db/pelagios-api.db"

Activate the postgres driver and adapt username and password settings:

    # Postgres configuration example
    db.default.driver="org.postgresql.Driver"
    db.default.url="jdbc:postgresql://localhost/peripleo"
    db.default.user="peripleo_user"
    db.default.password="arkiv"

### Install play

    cd /srv/pelagios
    wget https://downloads.typesafe.com/play/2.2.4/play-2.2.4.zip
    unzip play-2.2.4.zip
    cd peripleo/
    
### Run peripleo

    /srv/pelagios/play-2.2.4/play start

## Install solr
    
  Note: SolR version 6.1.0 requires [Java 8](http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html).

  Install SolR:

    user="user"
    group="group"
    solr_version="6.1.0"
    SOLR_INSTALL_DIR=/path/to/solr/install/dir
    cd ${SOLR_INSTALL_DIR}
    
    sudo wget http://archive.apache.org/dist/lucene/solr/${solr_version}/solr-${solr_version}.tgz
    sudo tar -xzvf solr-${solr_version}.tgz
    sudo chown -R ${user}:${user} solr-6.1.0
  
  Create SOLR_HOME directory:
    
    SOLR_HOME = "/path/to/solrhome"
    sudo mkdir ${SOLR_HOME}
    sudo chown ${user}:${user} ${SOLR_HOME}
    
  Copy solr.xml to SOLR_HOME:
  
    cp ${SOLR_INSTALL_DIR}/server/solr/solr.xml ${SOLR_HOME}    
    
  Create core directory in SOLR_HOME:
  
    sudo -u ${user} mkdir ${SOLR_HOME}/newcore
    
  Copy data driven schema configuration:
    
    cp -R ${SOLR_INSTALL_DIR}/server/solr/configsets/data_driven_schema_configs/conf ${SOLR_HOME}/newcore
    
  Copy SolR service configuration file and adapt settings:
    
    sudo cp ${SOLR_INSTALL_DIR}/bin/solr.in.sh /etc/default/solr.in.sh
    
  Define the Java Home directory in`/etc/default/solr.in.sh`:
  
    SOLR_JAVA_HOME="/path/to/jdk1.8.x_xxx"  
    
  Copy service initialization script and adapt settings:
    
    cp ${SOLR_INSTALL_DIR}/bin/init.d/solr /etc/init.d/
    
  Activate Solr configuration in `${SOLR_INSTALL_DIR}bin/solr`:
  
    SOLR_INCLUDE="/etc/default/solr.in.sh"
  
  Create new core:
    
    sudo ${SOLR_INSTALL_DIR}/bin/solr create_core -c earkstorage

## Installing earkweb 

1. Checkout project

        git clone https://github.com/eark-project/earkweb
        
    Optionally, define the earkweb root directory in the environment variable EARKWEB:

        cd earkweb
        export EARKWEB=`pwd`
    
    If this variable is set, it can be used to execute commands explained further down in this README file.

2. Create virtual environment (python)

    Install virtual environment python packages (requires pip: https://pypi.python.org/pypi/pip):

        sudo pip install virtualenv
        sudo pip install virtualenvwrapper

    Create a directory for your virtual environments and set the environment variable (e.g. in your ~/.bashrc):

        mkdir ~/Envs
        export WORKON_HOME=~/Envs
        source /usr/local/bin/virtualenvwrapper.sh

    Create a virtual environment (e.g. named earkweb) to install additional python packages separately from the default python installation.
    
        mkvirtualenv earkweb
        
    If the virtual environment is active, this is shown by a prefix in the console (type `workon earkweb` otherwise):
    
        (earkweb)user@machine:~$

    The virtual environment can be deactivated again by typing:
    
        deactivate

3. Install additional debian packages:

        sudo apt-get install libmysqlclient-dev libffi-dev unixodbc-dev python-lxml libgeos-dev
        sudo pip install --upgrade pytz

4. Install additional python packages:

        pip install -r ${EARKWEB}/requirements.txt
        
5. Create directories and files making sure the user running earkweb has rights to read and write:

        sudo mkdir -p /var/data/earkweb/{reception,storage,work,access}
        sudo mkdir /var/data/earkweb/storage/pairtree_root
        sudo touch /var/data/earkweb/storage/pairtree_version0_1
        sudo chown -R <user>:<group> /var/data/earkweb/
        sudo mkdir -p /var/log/earkweb
        sudo chown <user>:<group> /var/log/earkweb
        
6. Rename sample config file `config/settings.cfg.sample` to `config/settings.cfg` and adapt settings according to your environment.

## Create and initialize database

1. Prepare databases (one main database for the frontend (eark) and one for the celery backend (celerydb):

    Install mysql database if not available on your system:
    
        sudo apt-get install mysql-server
    
    A MySQL database is defined in `${EARKWEB}/settings.py`.
    Create the database first and 
    
    Login to mysql:
    
        mysql -u root -p<rootpassword>
        
    Create user 'arkiv':
    
        CREATE USER 'arkiv'@'%' IDENTIFIED BY 'arkiv';
        
    Create database 'eark':
        
        mysql> create database eark;
        
    Grant access to user 'arkiv':

        GRANT ALL ON eark.* TO arkiv@'%' IDENTIFIED BY 'arkiv';

2. Create database schema based on the model and apply initialise the database:

        python manage.py makemigrations
        python manage.py migrate

    Required software packages for django/celery/mysql support:

        pip install django
        pip install -U celery
        pip install django-celery
        pip install MySQL-python
        
3. Once the database is running, tasks need to be registered in the database. To do so run the following script in the `${EARKWEB}` directory:

        python ./workers/scantasks.py

4. Create a user

        python ./util/createuser.py eark user@email eark true

## Run update script

To update EARKweb, the Solr instance and perform database migrations, do the following:

    cd ${EARKWEB}
    python autoupdate.py
    
If you are using the VM version, simply use the `Update E_ARK Web` desktop shortcut (which will do a `git pull` and
do everything that is needed to apply the updates).

## Celery distributed task execution 

1. Start the daemon from command line (development mode):
    
        cd ${EARKWEB}
        python manage.py celeryd -E -Ofair
        
    For development it is recommended to enable the CELERY_ALWAYS_EAGER property in earkweb/settings.py:

        #CELERY_ALWAYS_EAGER = True
        
    By this way the celery tasks run in the same process which allows debugging.
        
# Run in development mode

This section explains how to run *earkweb* in development mode.

1. Change to the *earkweb* directory:

        cd <earkweb_install_path>/earkweb
        
2. Start web application

    Start the web application from the command line using the command:

        python manage.py runserver
        
    A message similar to the one below should be shown in case of success
    
        System check identified no issues (0 silenced).
        June 18, 2015 - 08:34:56
        Django version 1.7, using settings 'earkweb.settings'
        Starting development server at http://127.0.0.1:8000/
        Quit the server with CONTROL-C.
        
    Open web browser at http://127.0.0.1:8000/
