# Developer notes

## Installation

Follow the manual installation procedure to set-up the development environment:

* [Manual installation](./install_manual.md) 

## Project layout

* celery - Celery configuration and daemon start script
* config - Configuration files (main configuration file is configuration.py)
* earkcore - Generic functionality, can be released as an independent module 
* earkweb - Django/celery setup and configuration
* resources - E-ARK resources (schemas etc.)
* search - Django web-gui module for search and DIP creation
* sip2aip -Django web-gui module for SIP to AIP conversion
* static - Static content of the web application (javascript, css, etc.)
* templates - Base template files
* util - Utility scripts
* workers - Celery tasks
* workflow - Django web-gui module 

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
    