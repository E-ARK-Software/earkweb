# Manual installation

Step-by-step manual installation.

## Install dependencies

### Debian packages

    sudo apt-get install python3 python3-dev python3-virtualenv build-essential default-libmysqlclient-dev summain
    
### Message queue and result backend

Install result backend database:

    sudo apt-get install redis-server

### SolR

This section only applies if SolR is used as a search module.
    
Note: SolR version 8.4.1 requires at least Java 8 (current version: [Java 13](https://www.oracle.com/java/technologies/javase-jdk13-downloads.html)).

1. Install SolR:

       SOLR_VERSION="8.4.1"
       SOLR_INSTALL_DIR="/opt/solr"
       sudo mkdir $SOLR_INSTALL_DIR
       sudo chown -R ${USER}:`id -gn` $SOLR_INSTALL_DIR
       cd ${SOLR_INSTALL_DIR}
       wget http://archive.apache.org/dist/lucene/solr/${SOLR_VERSION}/solr-${SOLR_VERSION}.tgz
       tar -xzvf solr-${SOLR_VERSION}.tgz
  
2. Create SOLR_HOME directory:
    
       SOLR_HOME = "/var/data/solr"
       sudo mkdir -p ${SOLR_HOME}
       sudo chown ${USER}:`id -gn` ${SOLR_HOME}
    
3. Copy solr.xml to SOLR_HOME:
  
       cp ${SOLR_INSTALL_DIR}/server/solr/solr.xml ${SOLR_HOME}    
       
4. Create core `storagecore1`

        cd ${SOLR_INSTALL_DIR}
        ./bin/solr create_core -c storagecore1
        
5. Enable remote streaming

        curl http://localhost:8983/solr/storagecore1/config -H 'Content-type:application/json' -d '{
            "set-property": [{
                "requestDispatcher.requestParsers.enableRemoteStreaming": true
            },
            {
                "requestDispatcher.requestParsers.enableStreamBody": true
            }
            ]
        }'

6. Configuring the ExtractingRequestHandler in `solrconfig.xml`

    If you have started Solr with one of the supplied example configsets, you already have the ExtractingRequestHandler 
    configured by default and you only need to customize it for your content.
    
    If you are not working with an example configset, the jars required to use Solr Cell will not be loaded automatically. 
    You will need to configure your `solrconfig.xml` to find the ExtractingRequestHandler and its dependencies: 
        
        <lib dir="${solr.install.dir:../../..}/contrib/extraction/lib" regex=".*\.jar" />
        <lib dir="${solr.install.dir:../../..}/dist/" regex="solr-cell-\d.*\.jar" />
    
    You can then configure the ExtractingRequestHandler in `solrconfig.xml` The following is the default configuration 
    found in Solr’s _default configset, which you can modify as needed:
    
        <requestHandler name="/update/extract"
                        startup="lazy"
                        class="solr.extraction.ExtractingRequestHandler" >
          <lst name="defaults">
            <str name="lowernames">true</str>
            <str name="fmap.content">_text_</str>
          </lst>
        </requestHandler>
        
7. Run configuration script

       python3 ./utils/scripts/init_solr.py
       
## earkweb 

1. Checkout project

       git clone $repository/earkweb
        
    Change to earkweb directory:

       cd earkweb
    
2. Create virtual environment (python)

       virtualenv -p python3 venv

4. Install additional python packages:

       pip3 install -r requirements.txt
       
   Note that local library dependencies can be installed using pip with the '-e' parameter. In this case changes in the 
   dependant library take effect immediately:

       pip install -e ../otherlib/.    
        
5. Manually install additional packages:

    Optional: This step only applies if file format identification should be done during ingest.

    [Fido](https://github.com/openpreserve/fido) is used for file format identification (mime-type and PRONOM Unique Identifier).

   1. Install fido:

          wget https://github.com/openpreserve/fido/archive/1.3.2-81.tar.gz
          tar -xzvf 1.3.2-81.tar.gz
          cd fido-1.3.2-81
          python setup.py install

   2. Update filetype signatures (long running):

          cd fido
          python update_signatures.pymy

    Ghostscript (PDF to PDF/A conversion)

   1. Download: [Ghostscript 9.18] (http://downloads.ghostscript.com/public/ghostscript-9.18.tar.gz):
    
        wget http://downloads.ghostscript.com/public/old-gs-releases/ghostscript-9.18.tar.gz

   2. Installation: [how to install] (http://www.ghostscript.com/doc/9.18/Install.htm):

        tar -xzf ghostscript-9.18.tar.gz
        cd ghostscript-9.18
        ./configure
        make
        sudo make install
        
6. Create directories and files making sure the user running earkweb has rights to read and write (you have to replace 
`$USER` and `$GROUP` or set the variables  accordingly):

        sudo mkdir -p /var/data/earkweb
        sudo chown -R $USER:$GROUP /var/data/earkweb/
               
        mkdir -p /var/data/earkweb/storage/pairtree_root
        touch /var/data/earkweb/storage/pairtree_version0_1
       
        sudo mkdir -p /var/log/earkweb
        sudo chown $USER:$GROUP /var/log/earkweb
        mkdir -p /var/log/celery
        
        
7. Rename sample config file `settings/settings.cfg.default` to `settings/settings.cfg` and adapt settings according to your environment.

## Create and initialize database

1. Prepare databases (one main database for the frontend (earkweb) and one for the celery backend (celerydb):

    Install mysql database if not available on your system:
    
       sudo apt-get install mysql-server
    
    Login to mysql:
    
       mysql -u root -p
        
    Create user 'repo':
    
       CREATE USER 'repo'@'%' IDENTIFIED BY 'repo';
        
    Create database 'repodb in mysql console:
        
       create database repodb;
        
    Grant access to user 'repo'  mysql console:

       GRANT ALL ON repodb.* TO repo@'%' IDENTIFIED BY 'repo';

2. Exit mysql console and create the database tables (first Django tables, then module tables):

    Adapt MySQL database settings in `settings/settings.cfg` and then create the tables:
    
       python manage.py makemigrations earkweb
       python manage.py migrate

4. Create a user (user name, email, password, super user status) using the Django function:

       python manage.py createsuperuser
        
5. Create token for admin user 

Open a Django shell using command `python manage.py shell` and execute the following commands (adapt primary key of the user if necessary: `pk`):

    from django.contrib.auth.models import User
    u = User.objects.get(pk=1)
    from rest_framework.authtoken.models import Token
    token = Token.objects.create(user=u)
    token.save()

Documentation: http://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication

## Celery distributed task execution 

### Install message queue and result backend

Install message queue:

    sudo apt-get install rabbitmq-server

Install result backend database:

    sudo apt-get install redis-server

### Start celery daemon and flower monitoring

1. Start the daemon from command line (development mode):
    
       celery multi start ingestqueue -A earkweb.celery -Ofair --pidfile=/tmp/default_worker.pid --logfile=/tmp/default_worker.log
        
    Celery status should give the following info:
    
       celery -A earkweb.celery status
       ingestqueue@N3SIM1412: OK
        
       1 node online.
        
    The celery worker can be stopped using the following command:
    
       celery -A earkweb.celery control shutdown
        
2. Start flower monitoring service:

    In the development environment, flower can be started using the following command (broker redis):

       celery -A earkweb.celery flower --address=127.0.0.1 --port=5555 --broker=redis://localhost
       
    or (broker rabbitmq):
    
       celery -A earkweb.celery flower --address=127.0.0.1 --port=5555 --broker=amqp://guest:guest@localhost:5672
        
# Run in development mode

This section explains how to run *earkweb* in development mode.

1. Change to the *earkweb* directory:

       cd <earkweb_install_path>/earkweb
        
2. Start web application

    Start the web application from the command line using the command:

       python manage.py runserver 0.0.0.0:8000
        
    A message similar to the one below should be shown in case of success
    
       System check identified no issues (0 silenced).
       June 18, 2015 - 08:34:56
       Django version 1.7, using settings 'earkweb.settings'
       Starting development server at http://127.0.0.1:8000/
       Quit the server with CONTROL-C.
       
    Open web browser at http://127.0.0.1:8000/

# Additional configuration steps

1. Configure API key:

    http://127.0.0.1:8000/earkweb/adminrest_framework_api_key/apikey/
    
    And make sure it matches the parameter `backend_api_key` in the configuration file `settings/settings.cfg`. 