# NLP documentation

## General

The NLP tools that are currently implemented or will be added in the near future make use of the Celery backend, so
you do not require a completely different technology stack. There are however a few extra dependencies that require
a small amount of extra work to set up.

## NLP tools overview

### Current

* [Stanford NER] (http://nlp.stanford.edu/software/CRF-NER.shtml): Named Entity Recognition, adaptable to language and domain with different classifiers.

### Planned

* Text categorisation: Identify the abstract topic of a text using a pre-trained model.

## Usage

The NLP tools can be used from the earkweb interface. *TODO*

## Requirements

A standard earkweb installation will be sufficient. A Celery backend, a running Solr instance and Java are required. Only
packages that have been indexed by Solr can be used as input for the NLP tools.

## Installation

Set up folder structure:
    
    sudo mkdir -p /var/data/earkweb/nlp/stanford
    sudo chown -R <user>:<group> /var/data/earkweb/nlp
    
[Download the Stanford NER] (http://nlp.stanford.edu/software/CRF-NER.shtml#Download) and unpack it into the directory 
you just created. It should be usable out of the box and comes with three different classifiers for English texts. Additional
classifiers can be installed by putting the `.ser.gz` file in the `classifiers/` subfolder.
 
Next, install python dependencies (from the virtual environment!): [NLTK] (http://www.nltk.org/data.html)

*TODO*
