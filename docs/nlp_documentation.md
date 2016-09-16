# NLP documentation

## General

The NLP tools that are currently implemented or will be added in the near future make use of the Celery backend, so
you do not require a completely different technology stack. There are however a few extra dependencies that require
a small amount of extra work to set up.

## NLP tools overview

### Stanford NER 

Currently, we implemented [Stanford NER] (http://nlp.stanford.edu/software/CRF-NER.shtml): Named Entity Recognition, 
adaptable to language and domain with different classifiers.
* This can be performed on indexed files containing text (PDF, Word, ...). The results are added to the Solr index as a 
`_strings_` field, which means you can search for it. Any match will be an exact match, not a partial one.

### Planned

* Text categorisation: Identify the abstract topic of a text using a pre-trained model.

## Requirements

A standard earkweb installation will be sufficient. A Celery backend, a running Solr instance and Java are required. Only
packages that have been indexed by Solr can be used as input for the NLP tools.

## Installation

In case this was not done during the earkweb installation, create the following folder structure:
    
    sudo mkdir -p /var/data/earkweb/nlp/stanford
    sudo mkdir -p /var/data/earkweb/nlp/storage
    
    sudo chown -R <user>:<group> /var/data/earkweb/nlp
    
[Download the Stanford NER] (http://nlp.stanford.edu/software/CRF-NER.shtml#Download) and unpack it into the directory 
you just created. It should be usable out of the box and comes with three different classifiers for English texts. Additional
classifiers can be installed by putting the `.ser.gz` file in the `/var/data/earkweb/nlp/stanford/classifiers` subfolder.

The folder structure should look like this:

    /var/data/earkweb/nlp/stanford/     # the .jar files must be here
    |-- classifiers/                    # the .ser.gz files must be here
    
### Configuration

The config file `settings.cfg` has a section called `[nlp]`. They are currently set to default values, you are free to
change them, but remember to create the folder structure accordingly!

    nlp_solr_server_ip = solr
    nlp_solr_port = 8983
    nlp_solr_core = earkstorage
    stanford_jar_path = /var/data/earkweb/nlp/stanford                      # the location of stanford.jar files
    stanford_models_path = /var/data/earkweb/nlp/stanford/classifiers       # subfolder for .ser.gz files (NER models)
    category_models_path = /var/data/earkweb/nlp/textcategories/models 
    config_path_nlp = /var/data/earkweb/nlp                                 # general folder
    tar_path = /var/data/earkweb/nlp/storage                                # here .tar containers are stored that can be used as source for NLP tasks

## Usage

The NLP tools can be used from the earkweb interface. Currently there is no navbar entry (because it needs a manual 
setup), so you manually have to access it via the URL: `[...]/earkweb/datamining/start`.

There are two different options to use it:

* _New collection:_ Add a package identifier, the file format you want to use (`application/pdf` for example - must match Solr index entry)
and a name for the tarfile, `example.tar`. This file will be created at the `tar_path` value you can change in the
settings file.
* _Existing collection:_ The input required is the name of an existing tar file, that has previously been created by the
first option. With this, you can use the same data with a different model, for example.

### How it works

Depending on the two input methods above, either a new tar file is created or an existing one is used. This does not affect
how the tasks work.

Every file stored in the tar file has its Solr path as the file name, and can thus be identified independently from external
information (provided the Solr index does still exist). No matter the original file format that was ingested, those files
are all plain text files, so no additional processing step is required. 

#### NER:

The NER model selected in the web interface is used to tag the files. The result of this is - subject to the assigned NER
classes - further processed. Currently, entities tagged as `LOC`, `ORG` and `PER` (location, organisation, person) are used.
The Solr index entry for the specific file is updated with these entities; the fields are `locations_ss`, `organisations_ss`
and `persons_ss` respectively. The `_ss` suffix turns them into an array of strings, which have to match the query aimed
at that field exactly to return a result.

# Known issues/TODOs

* <s>There is no feedback after a task is started. This includes error messages, status updates...</s>
* Basic feedback is there, but we need info on the tasks next.
* It is not checked whether a given tar file already exists.
* NLP results can not be searched for through the earkweb interface (it is possible using Solr directly).
 