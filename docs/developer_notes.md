# Developer notes
  
## Installation

Clone the project from the Github/Gitlab repository and follow either the Docker installation instructions:

* [Install using Docker](./install_docker.md)

The `Dockerfile` for earkweb loads the source code from earkweb's root directory. 

Or install the system manually:

* [Manual installation](./install_manual.md) 

## Project overview

* access - Django web-gui module for access
* administration - Administration area
* api - REST API
* config - Configuration for all modules
* docker - docker resources
* docs - Documentation
* celery - Celery configuration
* earkweb - Django/celery main app and configuration, functions for all modules
* taskbackend - Celery tasks
* health - Application health check functions
* locale - Localization/translation files
* management - Django web-gui module for data management
* resourcesync - harvesting interface based on resource sync
* settings - configuration files (input for config)
* static - Static content of the web application (javascript, css, etc.)
* submission - Django web-gui module for submission
* templates - Base template files
* util - Utility scripts

## Monitoring tasks

Install `flower` using pip (`pip install flower`). 
 
In the development environment, flower can be started using the following command:

    celery flower --address=127.0.0.1 --port=5555 --broker=redis://localhost
    
Access flower service in your web browser at the following URL:

    http://127.0.0.1:5555
    
If the flower service is available in a sub-path (e.g. http://127.0.0.1/flower), then a URL prefix needs 
to be defined when starting the service:

    celery flower -A earkweb --address=127.0.0.1 --url_prefix=flower --port=5555 --broker=redis://localhost

## Internationalization and language support

Generate language files for supported languages:

    django-admin makemessages -l de
    django-admin makemessages -l en
    
Compile language files:

    django-admin compilemessages
