# earkweb

E-ARK integrated prototype web application

## Dependencies

### Debian-based linux

* [jhove](https://packages.debian.org/jessie/jhove)
* [summain](https://packages.debian.org/jessie/summain)

Install packages:

    sudo apt-get install summain jhove

### Python modules

* [fido](https://github.com/openpreserve/fido) 

Install fido:

    wget https://github.com/openpreserve/fido/archive/1.3.2-81.tar.gz
    tar -xzvf 1.3.2-81.tar.gz
    cd fido-1.3.2-81
    sudo python setup.py install

## Set up the development environment

### Checkout and install dependencies

1. Checkout project

        git clone https://github.com/eark-project/earkweb
        
    Optionally, define the earkweb root directory in the environment variable EARKWEB:

        cd earkweb
        export EARKWEB=`pwd`
    
    If the variable is set, it can be used to execute commands explained in this README.

2. Create virtual environment (python)

    Create a virtual environment (e.g. named earkweb) to install additional python packages separately from the default python installation.

        sudo pip install virtualenv
        sudo pip install virtualenvwrapper
        mkvirtualenv earkweb
        workon earkweb
        
    If the virtual environment is active, this is shown by a prefix in the console:
    
        (earkweb)user@machine:~$
        
    If it is not active, it can be activated as follows:
    
        user@machine:$~$ workon earkweb

    And it can be deactivated again by typing:
    
        deactivate

3. Install additional libraries

        pip install -r ${EARKWEB}/requirements.txt

4. Enable CAS in Django

    Install the django-cas package.

    4.1. Install mercurial if it is not available already:

        sudo apt-get install mercurial

    4.2 Get module from https://bitbucket.org/cpcc/django-cas

        hg clone https://bitbucket.org/cpcc/django-cas
    
    4.3. Install django-cas

        cd django-cas
        python setup.py install

### Prepare database and execute

1. Prepare database

    A MySQL database is defined in `${EARKWEB}/settings.py`.
    Create the database first and grant access to user 'arkiv':
    
        mysql -u root -p<rootpassword>
        
        mysql> create database eark;
        Query OK, 1 row affected (0.00 sec)

        mysql> GRANT ALL ON eark.* TO arkiv@localhost IDENTIFIED BY 'arkiv';

2. Create database schema based on the model and apply initialise the database:

        python manage.py makemigrations
        python manage.py migrate
    
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
    
### Create directories

    sudo mkdir -p /var/data/earkweb/{reception,storage,work,ingest}
    sudo chown -R <user>:www-data /var/data/earkweb/
    sudo chmod -R g+w /var/data/earkweb/

## Celery services

### Start daemon

make sure the virtual environment "earkweb" is active (prefix "earkweb" in terminal) and change to the earkweb directory:

    (earkweb)<user>@<machine>:~/$ cd ${EARKWEB}    

Start the daemon from command line:
    
    celery --app=earkweb.celeryapp:app worker

or use the daemon script as super user:

    sudo ./celery/celeryd/celeryd start
    celery init v10.0.
    Using config script: /opt/python_wsgi_apps/earkweb/celery/etc/celeryd
    celery multi v3.1.18 (Cipater)
    > Starting nodes...
	> worker1@<machine>: OK

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
    >>> from workers.tasks import SomeCreation
    >>> result = SomeCreation().apply_async(('testparam',), queue='default')
    >>> result.status
    'SUCCESS'
    >>> result.result
    'Parameter: testparam'
    >>> 

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