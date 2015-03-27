# access_dipcreator
Web application for creating DIPs based on selected AIPs

## Enable authentication using CAS

### Prepare Apache Tomcat (enable SSL)

1. Create keystore

    keytool -genkey -alias tomcat -keyalg RSA -keystore keystore.jks

2. Activate SSL using the keystore (in conf/server.xml):

    <Connector port="8443" 
        keystoreFile="/usr/local/java/apache-tomcat-7.0.56/keystore.jks" 
        keystorePass="changeit" 
        protocol="org.apache.coyote.http11.Http11NioProtocol"
        maxThreads="150" SSLEnabled="true" scheme="https" secure="true"
        clientAuth="false" sslProtocol="TLS" />

### Deploy CAS

1. Download CAS

    http://downloads.jasig.org/cas/cas-server-4.0.0-release.tar.gz

2. Deploy CAS WAR to Apache Tomcat.

    cp cas-server-4.0.0/modules/cas-server-webapp-4.0.0.war $TOMCAT_HOME/webapps/

### Enable CAS in Django 

1. Get module from https://bitbucket.org/cpcc/django-cas
