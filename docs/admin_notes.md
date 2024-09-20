# Admin notes

## Automatic start of services using supervisor

Supervisor is a process control system that allows you to manage and monitor processes. This guide helps you install and configure a basic service.

### 1. Install Supervisor

First, install Supervisor using your package manager:

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install supervisor
```

#### CentOS/RHEL:
```bash
sudo yum install epel-release
sudo yum install supervisor
```

Enable and start the Supervisor service:

```bash
sudo systemctl enable supervisor
sudo systemctl start supervisor
```

### 2. Configure services

Create configuration files for the earkweb services in `/etc/supervisor/conf.d/`.

#### Celery 

Celery is an open-source, distributed task queue that allows you to run time-consuming or periodic tasks in the background, making it ideal for asynchronous job execution in Python applications.

```bash
sudo nano /etc/supervisor/conf.d/celery.conf
```

Add the following configuration, modifying paths and user as needed:

```ini
[program:celery]
directory=/opt/earkweb
command=/opt/earkweb/start_celery.sh
user = user
group = users
stdout_logfile = /var/log/earkweb/celery.log
stderr_logfile = /var/log/earkweb/celery.err
autostart = true
```

#### Celery beat

Celery Beat is a scheduler that runs alongside Celery workers to execute periodic tasks at specified intervals.

```bash
sudo nano /etc/supervisor/conf.d/beat.conf
```

Add the following configuration, modifying paths and user as needed:

```ini
[program:beat]
directory=/opt/earkweb
command=/opt/earkweb/start_beat.sh
user = user
group = users
stdout_logfile = /var/log/earkweb/beat.log
stderr_logfile = /var/log/earkweb/beat.err
autostart = true
```

#### Flower (Celery)

Flower is a real-time web-based monitoring tool for Celery that provides detailed insights into task progress, worker status, and system performance.

```bash
sudo nano /etc/supervisor/conf.d/flower.conf
```

Add the following configuration, modifying paths and user as needed:

```ini
[program:flower]
directory=/opt/earkweb
command=/opt/earkweb/start_flower.sh
user = user
group = users
stdout_logfile = /var/log/earkweb/flower.log
stderr_logfile = /var/log/earkweb/flower.err
autostart = true
```

#### Apache Solr

Apache Solr is an open-source search platform built on Apache Lucene, designed for full-text search and indexing capabilities.

```bash
sudo nano /etc/supervisor/conf.d/solr.conf
```

Add the following configuration, modifying paths and user as needed:

```ini
[program:solr]
directory=/opt/solr-8.4.1
command=/opt/solr-8.4.1/bin/solr start -f
user = user
group = users
stdout_logfile = /var/log/earkweb/solr.log
redirect_stderr=false
autostart = true
environment=SOLR_HOME=/opt/solr
environment=SOLR_INCLUDE=/opt/solr-8.4.1/bin/solr.in.sh
```

#### earkweb

Web application earkweb.

```bash
sudo nano /etc/supervisor/conf.d/earkweb.conf
```

Add the following configuration, modifying paths and user as needed:

```ini
[program:earkweb]
directory=/opt/earkweb
command=/opt/earkweb/start_earkweb.sh
user = user
group = users
stdout_logfile = /var/log/earkweb/earkweb.log
stderr_logfile = /var/log/earkweb/earkweb.err
autostart = true
stopsignal=INT
stopasgroup=true
killasgroup=true
```

### 3. Update Supervisor

After adding the configuration, tell Supervisor to pick up the new service:

```bash
sudo supervisorctl reread
sudo supervisorctl update
```

### 4. Manage Your Service

Start, stop, or check the status of your service:

```bash
sudo supervisorctl start myservice
sudo supervisorctl stop myservice
sudo supervisorctl status
```

### 5. Logs

You can monitor the logs for each of the service:

```bash
tail -f /var/log/myservice.log
```

### 6. Enable Supervisor on Boot

Ensure Supervisor starts on boot:

```bash
sudo systemctl enable supervisor
```

## API authentication

### Create API token for users

Open a Django shell using command `python manage.py shell` and execute the following commands (adapt primary key of the user: `pk`):

    from django.contrib.auth.models import User
    u = User.objects.get(pk=1)
    from rest_framework.authtoken.models import Token
    token = Token.objects.create(user=u)
    print token.key
    8d14d3383b181bf592f825df813874630f8de607

Documentation: http://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication

### Create API Keys

User independent API keys can be managed via the "djangorestframework-api-key" administration:

    http://localhost:8000/earkweb/adminrest_framework_api_key/apikey/

## Generate a pool of identifiers 

The system can use a pool of pre-generated identifiers which can be added or generated using the REST API function /earkweb/api/identifiers

It is also possible to generate identifiers in python as follows:

    from earkweb.models import InternalIdentifier
    import os
    for i in range(0, 100):
        InternalIdentifier.objects.create(identifier=os.urandom(20).encode('hex'), org_nsid=org_nsid)

If the identifier assignment step during ingest fails this can be because of no identifiers being available for a given 
organisation namespace.

## Index repository

Script for indexing the repository:

    python util/index-aip-storage.py
