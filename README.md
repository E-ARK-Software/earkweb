# earkweb

The project [E-ARK Web](https://github.com/eark-project/earkweb) is a web application together with a task execution system which allows synchronous and asynchronous processing of 
information packages by means of processing units which are called *tasks*. The purpose of E-ARK Web is, on the one hand, to provide a user interface for the integrated prototype 
in order to showcase archival information package transformation workflows which are being developed in the E-ARK project in an integrated way. On the other hand, the goal is to 
provide an architecture which allows reliable, asynchronous, and parallel creation and transformation of E-ARK information packages (E-ARK SIP, AIP, and DIP) integrated with 
E-ARK backend services for scalable and distributed search and access.


The components of the E-ARK Web project coordinate package transformations between the package formats SIP, AIP, and DIP, and uses [Celery](http://www.celeryproject.org), a 
distributed task queue, as its main backend. Tasks are designed to perform atomic operations on information packages and any dependency to a database is intentionally avoided to 
increase processing efficiency. The outcome and status of a task's process is persisted as part of the package. The E-ARK Web project also provides a web interface that allows one 
to orchestrate and monitor tasks by being loosely coupled with the backend. The backend can also be controlled via remote command execution without using the web frontend. The 
outcomes of operations performed by a task are stored immediately and the [PREMIS](http://www.loc.gov/standards/premis/) format is used to record digital provenance information. It 
is possible to introduce additional steps, for example, to perform a roll-back operation to get back to a previous processing state in case an error occurs.

![alt tag](https://raw.githubusercontent.com/eark-project/earkweb/master/doc/img/earkweb_home.png)

## Dependencies

### Debian packages

    sudo apt-get install summain jhove pdftohtml 
    
Python image conversion (pgmagick) requires (image display):    
    
    sudo apt-get install graphicsmagick
    sudo apt-get install libgraphicsmagick++1-dev libboost-python-dev
    
PDF to HTML conversion:

    pdftohtml

### Python modules

#### fido

[fido](https://github.com/openpreserve/fido)

Install fido:

    wget https://github.com/openpreserve/fido/archive/1.3.2-81.tar.gz
    tar -xzvf 1.3.2-81.tar.gz
    cd fido-1.3.2-81
    sudo python setup.py install

Update filetype signatures:

    cd fido
    python update_signatures.py

### Software packages for file migrations:

#### Ghostscript

Used for PDF to PDF/A conversion.

Download: [Ghostscript 9.18] (http://downloads.ghostscript.com/public/ghostscript-9.18.tar.gz)

Installation: [how to install] (http://www.ghostscript.com/doc/9.18/Install.htm)

    tar -xzf ghostscript-9.18.tar.gz
    cd ghostscript-9.18
    ./configure
    make
    make install

## Set up the development environment

### Checkout and install dependencies

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

    Create a virtual environment (e.g. named earkweb) to install additional python packages separately from the default python installation.
    
        mkvirtualenv earkweb
        workon earkweb

    Create a directory for your virtual environments and set the environment variable (e.g. in your ~/.bashrc):
    
        export WORKON_HOME=~/Envs
        source /usr/local/bin/virtualenvwrapper.sh
        
    If the virtual environment is active, this is shown by a prefix in the console:
    
        (earkweb)user@machine:~$
        
    If it is not active, it can be activated as follows:
    
        user@machine:$~$ workon earkweb

    And it can be deactivated again by typing:
    
        deactivate

3. Install additional libraries

        pip install -r ${EARKWEB}/requirements.txtlib
        
   Common errors that might occur during python package installation are missing linux package dependencies, 
   therefore it might be necessary to install following packages:
        
        sudo apt-get install libmysqlclient-dev libffi-dev unixodbc-dev python-lxml libgeos-dev
        sudo easy_install --upgrade pytz

4. Enable CAS in Django

    Install the django-cas package.

    4.1. Install mercurial if it is not available already:

        sudo apt-get install mercurial

    4.2 Get module from https://bitbucket.org/cpcc/django-cas

        hg clone https://bitbucket.org/cpcc/django-cas
    
    4.3. Install django-cas

        cd django-cas
        python setup.py install

### Create directories

    sudo mkdir -p /var/data/earkweb/{reception,storage,work,ingest,access}
    sudo chown -R <user>:<group> /var/data/earkweb/
    sudo mkdir -p /var/log/earkweb
    sudo chown <user>:<group> /var/log/earkweb
    
### Create and initialize database

1. Prepare databases

    Install mysql database if not available on your system:
    
        sudo apt-get install mysql-server
    
    A MySQL database is defined in `${EARKWEB}/settings.py`.
    Create the database first and 
    
    Login to mysql:
    
        mysql -u root -p<rootpassword>
        
    Create user 'arkiv':
    
        CREATE USER 'arkiv'@'localhost' IDENTIFIED BY 'arkiv';
        
    Create database 'eark':
        
        mysql> create database eark;
        
    Grant access to user 'arkiv':

        GRANT ALL ON eark.* TO arkiv@localhost IDENTIFIED BY 'arkiv';
        
    Create another database for Celery:
    
        mysql> create database celerydb;

    And grant rights to use datase celery for user 'arkiv':
    
        mysql> GRANT ALL ON celerydb.* TO arkiv@localhost IDENTIFIED BY 'arkiv';


2. Create database schema based on the model and apply initialise the database:

        python manage.py makemigrations
        python manage.py migrate

    Required software packages for django/celery/mysql support:

        pip install django
        pip install -U celery
        pip install django-celery
        pip install MySQL-python
    
### Run web application (development mode)

3. Start web application

    Start the web application from the command line using the command:

        python manage.py runserver
        
    A message similar to the one below should be shown in case of success
    
        System check identified no issues (0 silenced).
        June 18, 2015 - 08:34:56
        Django version 1.7, using settings 'earkweb.settings'
        Starting development server at http://127.0.0.1:8000/
        Quit the server with CONTROL-C.
        
    Open web browser at http://127.0.0.1:8000/
    

## Celery services

### Start daemon in development mode

Make sure the virtual environment "earkweb" is active (prefix "earkweb" in terminal) and change to the earkweb directory:

    (earkweb)<user>@<machine>:~/$ cd ${EARKWEB}    

Start the daemon from command line:
    
    celery --app=earkweb.celeryapp:app worker

### Celery service on server

In development mode, the service is running as long as the terminal is open.

Alternatively, adapt settings (e.g. user settings) in the config file:

    celery/etc/celeryd

Then create a celery config directory:

    sudo mkdir -p /etc/earkweb/celery
    sudo chown -R <user>:<group> /etc/earkweb

Copy the script to the configuration directory:

    cp celery/etc/celeryd /etc/earkweb/celery/
   
Then you can use the daemon script as super user:

    sudo ./celery/celeryd/celeryd start
    celery init v10.0.
    Using config script: /etc/earkweb/celery/celeryd
    celery multi v3.1.18 (Cipater)
    > Starting nodes...
	> worker1@<machine>: OK

### Task registration

Tasks need to be registered in the database. To do so run the following script:

    python ./workers/scantasks.py
    
### Check registered tasks

    celery -A earkweb.celeryapp:app inspect registered
    -> worker1@<machine>: OK
    *  earkweb.celeryapp.debug_task
    *  workers.tasks.SomeCreation
    *  workers.tasks.add
        
### Test task

    python manage.py shell
    Python 2.7.6 (default, Mar 22 2014, 22:59:56) 
    [GCC 4.8.2] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    (InteractiveConsole)
    >>> from workers.default_task_context import DefaultTaskContext
    >>>  dtc = DefaultTaskContext("fd6ab39e-8355-42ec-a2dc-bc4b1d9c1fd2", "/var/data/earkweb/work/fd6ab39e-8355-42ec-a2dc-bc4b1d9c1fd2", "SIPReset", None, {}, None)
    >>> from workers.tasks import SomeTaskImplementation
    >>> result = SomeTaskImplementation().apply_async((dtc,), queue='default')
    >>> result.status
    'SUCCESS'
    >>> result.result.task_logger.log
    ['SIPExtraction task e184fb78-6423-4a7a-997e-8a0d1ed55c67', 'Processing package fd6ab39e-8355-42ec-a2dc-bc4b1d9c1fd2', ...]
    >>> result.result.task_logger.err
    []
    >>> result.result.task_status
    0

## Deployment on demo server

### Configure as WSGI app

Edit `/etc/apache2/sites-enabled/000-default`, add the variable `WSGIScriptAlias` which marks the file 
path to the WSGI script, that should be processed by mod_wsgi's wsgi-script handler, define a daemon
process which allows running the wsgi app using a separate virtual environment, and add the earkweb 
Location statement:

    WSGIScriptAlias /earkweb /opt/python_wsgi_apps/earkweb/earkweb/wsgi.py

    WSGIDaemonProcess earkweb python-path=/opt/PyVirtEnvs/earkweb/lib/python2.7/site-packages:/opt/python_wsgi_apps/earkweb:/opt/python_wsgi_apps/earkweb/earkweb

    <Location /earkweb>
        WSGIProcessGroup earkweb
        WSGIApplicationGroup %{GLOBAL}
    </Location>
    
Further information on using Django with Apache and mod_wsgi:

    https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/modwsgi/
    
### Update demo server deployment

The deployed version is a copy from this Github repository, update is done by sending a pull request on the master branch:

    sudo -u www-data git pull origin master
    
If static files have been changed, run Django's 'collectstatic' command:

    python manage.py collectstatic
   
If tasks have been changed, run the update script:

    python ./workers/scantasks.py

## CAS server installation

The development version points to the CAS instance installed on the demo server, therefore this is not required for
development.

### Installation

#### Prepare Apache Tomcat (enable SSL)

1. Create keystore

    Create keystore using the following command:

        keytool -genkey -alias tomcat -keyalg RSA -keystore keystore.jks
        
    In the following questions set the Common Name (CN) to earkdev.ait.ac.at to avoid SSL errors of type 'hostname mismatch'.

2. Activate SSL:

    To activate SSL, create a connector using the keystore created previously (in conf/server.xml)

        <Connector port="8443" 
            keystoreFile="/usr/local/java/apache-tomcat-7.0.56/keystore.jks" 
            keystorePass="changeit" 
            protocol="org.apache.coyote.http11.Http11NioProtocol"
            maxThreads="150" SSLEnabled="true" scheme="https" secure="true"
            clientAuth="false" sslProtocol="TLS" />

        cp cas-server-4.0.0/modules/cas-server-webapp-4.0.0.war $TOMCAT_HOME/webapps/

#### CAS Deployment

1. Download CAS

        wget http://downloads.jasig.org/cas/cas-server-4.0.0-release.tar.gz

2. Deploy CAS WAR to Apache Tomcat

        cp cas-server-4.0.0/modules/cas-server-webapp-4.0.0.war $TOMCAT_HOME/webapps/
    
### Administration

#### Add/Change user

Users are managed in the deployerConfigContext.xml which is located at (variable $CATALINA_HOME must point to the installation directory of apache tomcat):

    $CATALINA_HOME/webapps/cas/WEB-INF/deployerConfigContext.xml
    
Users can be added by creating a new entry in the following bean definition:
   
    <bean id="primaryAuthenticationHandler"
          class="org.jasig.cas.authentication.AcceptUsersAuthenticationHandler">
        <property name="users">
            <map>
                <entry key="user" value="pwd"/>
                ...
            </map>
        </property>
    </bean>

# Development

## Project layout

* celery - Celery configuration and daemon start script
* config - Configuration files and model (models.py) - parameters can be initialised from database and a fallback value can be defined.
* earkcore - Generic functionality, can be released as an independent module 
* earkweb - Django/celery setup and configuration
* resources - E-ARK resources (schemas etc.)
* search - Django web-gui module 
* sip2aip -Django web-gui module 
* static - Static content of the web application
* templates - Base template
* workers - Celery tasks
* workflow - Django web-gui module 

## Test

Install py.test

    pip install -U pytest

Run all tests:

    py.test tasks lib

## Attributions

### WireIt

The workflow editor is based on WireIt which is distributed under the MIT License :

Copyright (c) 2007-2009, Eric Abouaf <eric.abouaf at gmail>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
