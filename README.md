# earkweb

## Introduction

[*earkweb*](https://github.com/E-ARK-Software/earkweb) is an open source repository for archiving digital objects. It 
offers basic functions for ingest, management and dissemination of information packages. 

The information package format is based on the 
[Common Specification for Information Packages (CSIP)](https://dilcis.org/specifications/common-specification) which
uses [METS](http://www.loc.gov/standards/mets/) to represent the structure of the information package and 
[PREMIS](http://www.loc.gov/standards/premis/) to record digital provenance information. 

*earkweb* offers functionality for the three types of information packages defined in the OAIS reference model: the 
Submission Information Package (SIP) which is the information sent from the producer to the archive, the Archival 
Information Package (AIP) which is the information stored by the archive, and the Dissemination Information Package 
(DIP) which is the information sent to a user when requested. The system allows executing different types of actions, 
such as information extraction, validation, or transformation operations, on information packages to support ingesting 
a SIP, archiving an AIP, and creating a DIP from a set of AIPs.

## Software architecture

*earkweb* consists of a frontend web application together with a task execution system based on 
[Celery](http://www.celeryproject.org) which allows synchronous and asynchronous processing of information packages by 
means of processing units which are called “tasks”. 

The following diagram illustrates the E-ARK Web components.

![architecture overview lightweight version](./docs/img/architecture_overview_lightweightversion.png)

The user interface represented by the box on top of the diagram is a 
[Python](https://www.python.org)/[Django](https://www.djangoproject.com)-based web application which allows  
managing the creation and transformation of information packages. It supports the complete archival package 
transformation pipeline, beginning with the creation of the Submission Information Package (SIP), over the conversion 
to an Archival Information Package (AIP), to the creation of the Dissemination Information Package (DIP) which is 
used to disseminate digital objects to the requesting user. Tasks can be assigned to Celery workers (green boxes with 
a "C") which share the same storage area and the result of the package transformation is stored in the information 
package’s working directory based on files. 

Full-text content included in information packages is indexed by SolR.

A [ResourceSync](http://www.openarchives.org/rs/toc) interface exposes the changelist of information packages managed 
by the repository.

## Installation

* [Manual installation](./docs/install_manual.md) 
* [Build and run using Docker](./docs/install_docker.md)
* [Installation as WSGI app (Apache Webserver frontend)](./docs/install_wsgi.md)

## User guide

* [Web user interface guide](./docs/user_guide_webui.md)
* [Headless task execution (without gui)](./docs/user_guide_remotetask.md)
* [REST API](./docs/api_guide.md)
* [Admin notes](./docs/admin_notes.md)
* [Developer notes](./docs/developer_notes.md)
