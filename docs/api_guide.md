# API Guide

A Swagger user interface for the API is available at:

http://localhost:8000/earkweb/api/

A user which is logged in can use the Swagger API to process information packages owned by this user.

## Api key authorization

An authorization token can be created for a user registered in earkweb which allows for using the API. See 
[admin notes](admin_notes.md), section "Create API token for existing user" for further information.

Each command must add the authentication token header:

    curl -H "Authorization: Token d0c62bf357698d3f3e70bdcc596e10fa1bf104bd"

## Usage examples

Prepare variables:

    export SERVER=http://127.0.0.1
    export PORT=8000

### Batch submission

A typical use case for the earkweb API is to ingest a series of submissions. This procedure is as follows:

* Initialise submissions by sending POST requests to the API function “submission” providing
at least the package name in the body of the request (<code>{"packagename": "package1"}</code>. 
Optionally, an external unique identifier can be provided: 
<code>{"packagename": "testpackage16", "extuid": "doi:10.17487/rfc"}</code>):

        curl -v -X POST -d '{"packagename": "package1"}' http://$SERVER:$PORT/earkweb/api/informationpackages/

* In case of success the HTTP response code is "201 CREATED" and a new process ID is returned which is required for 
uploading data in a subsequent step.

        {"message": "Submission process initiated successfully.",
        "process_id": "cc3e95de-71d9-4e9e-8de7-128a1c92774f"}

* Upload data file (in this case a metadata file <code>metadata.xml</code> in DCAT format) to the submission (note that
the process ID returned by the previous request is used in this request to identify the target submission for the upload):

        curl -v -X POST -F "file=@/home/$USER/metadata.xml" http://$SERVER:$PORT/earkweb/api/cc3e95de-71d9-4e9e-8de7-
        128a1c92774f/metadata/upload

* In case of success, the response returns the SHA-256 hash sum of the uploaded data file:

        {"message": "File upload successfull", "sha256":
        "3f51c6557f02b73c23e381c1cae1861ec2d45b38080c24a6e8dd17fb0926f2
        1d"}

If large information packages need to be ingested, it is recommended to initialize a series of submissions first and 
then transfer the data directly to the storage directories of the corresponding submissions (e.g. copying files using 
ssh).

* Run ingest:

        curl -v -X POST http://$SERVER:$PORT/earkweb/api/informationpackages/cc3e95de-71d9-4e9e-8de7-128a1c92774f/startingest

