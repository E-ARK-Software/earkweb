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

The API allows creating data sets, uploading data, and start processing the data.

Each request must be executed with a user token header which is omitted in the query examples below for the sake of
readability:

    -H 'Authorization: Token $usertoken'

The procedure is as follows:

   1. Initialise a new data package:
   
          curl -X POST  -d 'package_name=genesis.harvest.scraped.20191024' http://$server:$port/earkweb/api/datasets/

      In case of success the HTTP response code is "201 CREATED" and a new process ID (`process_id`) is returned which 
      is required for uploading data in a subsequent step.

          {
              "process_id":"73483984-debd-4d04-a14c-5acb11167719",
              "work_dir":"/var/data/repo/work/73483984-debd-4d04-a14c-5acb11167719",
              "package_name":"dataset.001.20191024",
              "version":0,
              "last_change":"2020-03-20T15:38:23.026106+01:00"
          }
          
   2. Upload data file (here a CSV file /home/$user/datafile.csv (note that the process ID  (`process_id`) returned by 
      the previous request is used in this request to identify the target data set where the files are going to be 
      uploaded).
      
      For the first file of a representation only the process ID (`process_id`, here: 
      `73483984-debd-4d04-a14c-5acb11167719`) needs to be provided and the representation ID can be omitted:
   
          curl -F "file=@/home/$USER/datafile.csv" http://$server:$port/earkweb/api/datasets/73483984-debd-4d04-a14c-5acb11167719/data/upload/
    
      This will generate a random UUID identifier (`representationId`) for the representation which is returned as part 
      of the response message in case of success:
      
          {
              "message": "File upload successful",
              "sha256": "7c10a5a8e79989b608d5e63ed58c031676f43ee4cc01a00d013400941cf7f2d1",
              "processId": "73483984-debd-4d04-a14c-5acb11167719",
              "representationId": "5ed2c8b6-4f4b-46f7-a1f3-192472a76a41"
          }
          
      Additionally, the `sha265` hash sum allows verifying if the file was uploaded correctly.
      
      If a file needs to be added to a representation, the representation ID (`representationId`,  here: 
      `5ed2c8b6-4f4b-46f7-a1f3-192472a76a41`) is given as a parameter after the process ID.
    
          curl -F "file=@/home/$USER/datafile.csv" http://$server:$port/earkweb/api/datasets/73483984-debd-4d04-a14c-5acb11167719/5ed2c8b6-4f4b-46f7-a1f3-192472a76a41/data/upload/
          
      To upload metadata, a JSON metadata (`metadata.json`) file can be created:
      
          {
              "title": "Data set title",
              "description": "Data set description",
              "contactPoint": "Contact",
              "contactEmail": "contact@email.com",
              "publisher": "Publisher",
              "publisherEmail": "contact@email.com",
              "language": "English",
              "representations": {
                  "5ed2c8b6-4f4b-46f7-a1f3-192472a76a41": {
                      "distribution_label": "csv",
                      "distribution_description": "CSV table",
                      "access_rights": "limited"
                  }
              }
          }
          
      Note that if metadata for representations should be added, the representation ID in the metadata file must match the ID of the corresponding representation, e.g. 
      as in this example, the one created previously: `5ed2c8b6-4f4b-46f7-a1f3-192472a76a41`. 
      
      An example for a metadata upload request is the following:
      
          curl -F "file=@/home/$USER/metadata.json" http://localhost:8000/earkweb/api/datasets/cb755987-9e83-4e71-b000-dea9324e5dea/metadata/upload/

      which returns a similar response as the data file upload:
   
          {
              "message": "File upload successful", 
              "sha256": "7c10a5a8e79989b608d5e63ed58c031676f43ee4cc01a00d013400941cf7f2d1", 
              "processId": "73483984-debd-4d04-a14c-5acb11167719"
          }

   3. Store data:
   
          curl http://$server:$port/repo/api/datasets/cc3e95de-71d9-4e9e-8de7-128a1c92774f/startingest

      Once the data package is stored, it is indexed and gets an identifier of the form 
      "urn:uuid:f90668b9-112b-4723-8344-07449e7b657e".

      The data package can be changed afterwards which increases the version number and the index for the data package 
      is updated.

File upload does not have to be done via this API. It is possible to just create the data folders and transfer the data 
using other means of file transfer (scp, rsync, etc.).