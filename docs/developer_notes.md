# Developer notes

## Table of Contents

- [Developer notes](#developer-notes)
  - [Installation](#installation)
  - [Project layout](#project-layout)
  - [Unit tests](#unit-tests)
  
## Installation

Clone the project from the Github repository and follow either the Docker installation instructions:

* [Installing using Docker](./install_docker.md)

The Docker container for earkweb is loaded directly from the source directory. The Django server restarts automatically
if source code is changed, therefore it can be used as development instance.

Or install the system manually:

* [Manual installation](./install_manual.md) 

## Project overview

* celery - Celery configuration and daemon start script
* config - Configuration files (main configuration file is configuration.py)
* docker - Additional Docker related files
* docs - Documentation
* earkcore - Generic functionality, can be released as an independent module
* earkweb - Django/celery main app and configuration
* resources - E-ARK resources (schemas, test resources, etc.)
* search - Django web-gui module for search and DIP creation
* sip2aip - Django web-gui module for SIP to AIP conversion
* sipcreator - Django web-gui module for SIP creation
* static - Static content of the web application (javascript, css, etc.)
* templates - Base template files
* util - Utility scripts
* workers - Celery tasks
* workflow - Django web-gui module

## Debugging

If developing tasks which should be executed using the Celery backend, set the `CELERY_ALWAYS_EAGER` property in the
earkweb settings file `earkweb/settings.py` (uncomment existing code line):

    #CELERY_ALWAYS_EAGER = True

changing it to:

    CELERY_ALWAYS_EAGER = True

This will have the effect that Celery tasks are executed in the same process wich allows code debugging.

## Monitoring tasks

Install `flower` using pip (`pip install flower`) and start the tool using the following command: 
 
    celery flower -A earkweb --address=127.0.0.1 --port=5555
    
With prefix:

    celery flower -A earkweb --address==127.0.0.1 --url_prefix=flower --port=5555
    
Open web browser at:

  http://127.0.0.1:5555

## Unit tests 

Install py.test

    pip install -U pytest

Run one specific test class:

    (earkweb)user@machine:/path/to/earkweb$ py.test earkcore/storage/pairtreestorage.py
    ================================================================== test session starts =========================================================================================
    platform linux2 -- Python 2.7.6, pytest-2.9.1, py-1.4.31, pluggy-0.3.1
    rootdir: /path/to/earkweb, inifile: setup.cfg
    collected 7 items 
    
    earkcore/storage/pairtreestorage.py .......
    ================================================================== 7 passed in 0.48 seconds ====================================================================================

Run all tests:

    py.test tasks earkcore
    