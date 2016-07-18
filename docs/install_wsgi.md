# Deployment as WSGI app (Apache Webserver frontend)

## Table of Contents

  - [Install and Configure as WSGI app](#install-and-configure-as-wsgi-app)
  - [Celery service on server](#celery-service-on-server)
    - [Update server deployment](#update-server-deployment)
  - [Optional: CAS Single Sign On (SSO) installation](#optional-cas-single-sign-on-sso-installation)
    - [CAS Installation](#cas-installation)
      - [Prepare Apache Tomcat (enable SSL)](#prepare-apache-tomcat-enable-ssl)
      - [CAS Deployment](#cas-deployment)
      - [CAS Add/Change user](#cas-addchange-user)
      - [Enable CAS in Django](#enable-cas-in-django)

Django’s primary deployment platform is WSGI, the Python standard for web servers and applications.

## Install and Configure as WSGI app

### Install apache and mod wsgi

    sudo apt-get install libapache2-mod-wsgi
    
### Configure apache

Edit Apache web server configuration, e.g. `/etc/apache2/sites-enabled/000-default`, and add the variable `WSGIScriptAlias` which marks the file path to the WSGI script, that 
should be processed by mod_wsgi's wsgi-script handler, define a daemon process which allows running the wsgi app using a separate virtual environment, and add the earkweb 
Location statement:

    WSGIScriptAlias /earkweb /opt/python_wsgi_apps/earkweb/earkweb/wsgi.py

    WSGIDaemonProcess earkweb python-path=/opt/PyVirtEnvs/earkweb/lib/python2.7/site-packages:/opt/python_wsgi_apps/earkweb:/opt/python_wsgi_apps/earkweb/earkweb

    <Location /earkweb>
        WSGIProcessGroup earkweb
        WSGIApplicationGroup %{GLOBAL}
    </Location>
    
Further information on using Django with Apache and mod_wsgi:

    https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/modwsgi/
    
## Celery service on server

The celery service is configured in the following file:

    celery/etc/celeryd

Then create a celery config directory:

    sudo mkdir -p /etc/earkweb/celery
    sudo chown -R <user>:<group> /etc/earkweb

Copy the script to the configuration directory:

    cp celery/etc/celeryd /etc/earkweb/celery/
   
Then you can start/stop the daemon as follows:

    sudo ./celery/celeryd/celeryd start
    celery init v10.0.
    Using config script: /etc/earkweb/celery/celeryd
    celery multi v3.1.18 (Cipater)
    > Starting nodes...
	> worker1@<machine>: OK
	
This example shows how to run one single worker, multiple workers can be configured to allow distributed task execution.
    
### Update server deployment

The deployed on a server, the source code is a copy cloned from the Github repository, update is therefore possible by sending a pull request:

    sudo -u www-data git pull origin master
    
If static files have been changed, run Django's 'collectstatic' command which will copy static files (javascript, css, etc.) to the web servers static files directory:

    python manage.py collectstatic
   
If tasks have changed, run the update script:

    python ./workers/scantasks.py
    
The deploy.sh script is an example bash script which allows updating an installation:

    ./deploy.sh

## Optional: CAS Single Sign On (SSO) installation

Optionally, a CAS server can be used for authentication if Django authentication module is configured accordingly. 

### CAS Installation

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
    
#### CAS Administration

#### CAS Add/Change user

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

#### Enable CAS in Django

Install the django-cas package.

1. Install mercurial if required:

        sudo apt-get install mercurial

2. Get module from https://bitbucket.org/cpcc/django-cas

        hg clone https://bitbucket.org/cpcc/django-cas

3. Install django-cas

        cd django-cas
        python setup.py install

4. To configure CAS authentication in django, some changes to earkweb/settings.py are necessary:

    4.1 Add the following settings in the earkweb/settings.py:

        LOGIN_URL='/earkweb/accounts/login/'
    
        CAS_REDIRECT_URL = '/earkweb/search'
        LOGIN_URL = '/earkweb/accounts/login/'
        LOGOUT_URL = '/earkweb/accounts/logout/'
    
        CAS_SERVER_URL = 'https://<cas-service-server>:8443/cas/login'
    
    4.2. Add the following line to MIDDLEWARE_CLASSES:

        AUTHENTICATION_BACKENDS = (
            ...
            'django_cas.backends.CASBackend',
        )
   
    4.3. And the following two lines to MIDDLEWARE_CLASSES:
     
        MIDDLEWARE_CLASSES = (
            ...
            'django_cas.middleware.CASMiddleware', 
            'django.contrib.admindocs.middleware.XViewMiddleware', 
        )
