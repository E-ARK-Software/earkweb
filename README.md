# earkweb

## Table of Contents

- [Instroduction](#instroduction)
- [Installation](#installation)
- [User guide](#user-guide)

## Instroduction

[E-ARK Web](https://github.com/eark-project/earkweb) is an open source archiving and digital preservation system. It is 
[OAIS](http://public.ccsds.org/publications/archive/650x0m2.pdf)-oriented which means that data ingest, archiving and dissemination functions operate on information packages 
bundling content and metadata in contiguous containers. The information package format uses [METS](http://www.loc.gov/standards/mets/) to represent the structure and 
[PREMIS](http://www.loc.gov/standards/premis/) to record digital provenance information. 

E-ARK Web offers functionality for the three types of information packages defined in the OAIS reference model: the Submission Information Package (SIP) which is the information 
sent from the producer to the archive, the Archival Information Package (AIP) which is the information stored by the archive, and the Dissemination Information Package (DIP) which 
is the information sent to a user when requested. The system allows executing different types of actions, such as information extraction, validation, or transformation operations, 
on information packages to support ingesting a SIP, archiving an AIP, and creating a DIP from a set of AIPs.

E-ARK Web offers a leightweight frontend web application with [Celery](http://www.celeryproject.org) as a distributed task execution backend.

![earkweb home](./docs/img/earkweb_home.png)

The backend can also be controlled via [remote command execution](./docs/user_guide_remotetask.md) without using the web frontend. The outcomes of operations performed by a task 
are stored immediately so that the status information in the frontend's database can be updated afterwards. 
 


## Installation

* [Manual installation](./docs/install_manual.md) 
* [Installing using Docker](./docs/install_docker.md)
* [Installation as WSGI app (Apache Webserver frontend)](./docs/install_wsgi.md)
* [Developer notes](./docs/developer_notes.md)

## User guide

* [Web user interface guide](./docs/user_guide_webui.md)
* [Headless task execution (without gui)](./docs/user_guide_remotetask.md)

## NLP Natural Language Processing

E-ARK Web now offers NLP tools. Please check out the [NLP documentation] (./docs/nlp_documentation) if you are interested.