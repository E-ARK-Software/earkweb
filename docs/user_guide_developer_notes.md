# Developer notes

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