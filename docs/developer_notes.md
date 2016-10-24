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

Install `flower` using pip (`pip install flower`). 
 
In the development environment, flower can be started using the following command:

    celery flower -A earkweb --address=127.0.0.1 --port=5555
    
Access flower service in your web browser at the following URL:

  http://127.0.0.1:5555
    
If the flower service is available in a sub-path (e.g. http://127.0.0.1/flower), then a URL prefix needs to be defined when starting the service:

    celery flower -A earkweb --address=127.0.0.1 --url_prefix=flower --port=5555

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
    
## Adding fields to the Lily-Solr schema (Solr 4.10)

    cd /srv/lily-2.4/bin

Set environment variable:

    LILY_CONFIG=/srv/dm/dm-file-ingest/src/main/config/lily
    
Three files have to be updated:

1) schema.json: `$LILY_CONFIG/schema.json` - add to `fieldTypes`...

    {
      name: "eark$eadclevel_s",
      valueType: "STRING",
      scope: "non_versioned"
    }
    
and to `recordTypes`:

    {name: "eark$eadclevel_s", mandatory: false}

2) indexerconf.xml: `$LILY_CONFIG/indexerconf.xml`

    <field name="eadclevel_s" value="eark:eadclevel_s"/>

3) Edit `/srv/apache-solr-4.0.0/example/solr/eark1/conf/schema.xml`:

If you want to add a new field type according to the [Solr 4.10 field types](http://archive.apache.org/dist/lucene/solr/ref-guide/apache-solr-ref-guide-4.10.pdf) 
("Field Types Included with Solr"), add an entry like this to `<types>...</types>`:

    <fieldType name="date" class="solr.TrieDateField" precisionStep="8" positionIncrementGap="0"/>
    
For all other fields, add an entry to `<fields>...</fields>`:

    <field name="eadclevel_s" type="string" indexed="true" stored="true" required="false"/>
    
Now, load the updated schema files:

    ./lily-import -s $LILY_CONFIG/schema.json
    
Delete the old index:

    ./lily-update-index -n eark1 --state DELETE_REQUESTED

Add the index again:

    ./lily-add-index -n eark1 -c $LILY_CONFIG/indexerconf.xml -sm classic -s shard1:http://localhost:8983/solr/eark1 -dt eark1
    
Clear index:

    curl http://localhost:8983/solr/eark1/update/?commit=true -d "<delete><query>*:*</query></delete>" -H "Content-Type: text/xml"
    
Rebuild:

    ./lily-update-index -n eark1 --build-state BUILD_REQUESTED   
