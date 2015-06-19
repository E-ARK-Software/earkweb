# earkweb
E-ARK integrated prototype web application

## Set up the development environment

### Checkout and install dependencies

1. Checkout project

        git clone https://github.com/eark-project/earkweb

2. Create virtual environment (python)

    Create a virtual environment (e.g. named earkweb) to install additional python packages separately from the default python installation.

        sudo pip install virtualenv
        sudo pip install virtualenvwrapper
        mkvirtualenv earkweb
        workon earkweb
        
    If the virtual environment is active, this is shown by a prefix in the console:
    
        (earkweb)user@machine:~/path/to/earkweb$
        
    If it is not active, it can be activated as follows:
    
        user@machine:~/path/to/earkweb$ workon earkweb

    And it can be deactivated again by typing:
    
        deactivate

3. Install additional libraries

        pip install Django==1.7
        pip install requests
        pip install lxml

4. Adapt settings to your local development environment

    Change path so that it detects your local development path in earkweb/earkweb/urls.py:
    
        if "Development/" ...
    
    Set the file to "assume-unchanged":
    
        git update-index --assume-unchanged earkweb/earkweb/urls.py
    
    and undo if needed:
    
        git update-index --no-assume-unchanged earkweb/earkweb/urls.py

5. Enable CAS in Django

    Note that the CAS URL setting points to the development server, therefore it is not required
    to install CAS in the development environment.

    5.1. Install mercurial if it is not available already:

        sudo apt-get install mercurial

    5.2 Get module from https://bitbucket.org/cpcc/django-cas

        hg clone https://bitbucket.org/cpcc/django-cas
    
    5.3. Install django-cas

        cd django-cas
        python setup.py install

### Prepare database and execute

1. Prepare database

    A local SQLite database 'db.sqlite3' will be created in the project root directory.

        python manage.py migrate
    
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

## Deployment on demo server

### Configure as WSGI app

Edit `/etc/apache2/sites-enabled/000-default` and add the variable `WSGIScriptAlias` which marks the file 
path to the WSGI script, that should be processed by mod_wsgi's wsgi-script handler.:

    WSGIScriptAlias /earkweb /path/to/earkweb/earkweb/wsgi.py

A request for http://earkdev.ait.ac.at/earkweb in this case would cause the server to run the WSGI application defined in /path/to/wsgi-scripts/earkweb.

Additionally create variable `WSGIPythonPath` which defines a directory where to search for Python modules. 

    WSGIPythonPath /home/shsdev/python_wsgi_apps/access_dipcreator

And create a directory entry:

    <Directory /path/to/earkweb>
        Options Indexes FollowSymLinks MultiViews
        <Files wsgi.py>
            Order allow,deny
            allow from all
        </Files>
    </Directory>
    
Further information on using Django with Apache and mod_wsgi:

    https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/modwsgi/

## CAS server installation

The development version points to CAS installed on the demo server, therefore this is not needed for
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

#### Deployment

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