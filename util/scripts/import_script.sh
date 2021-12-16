#!/usr/bin/env bash
# required: libreoffice, jq, highlight.sh


# server
SERVER=localhost
PORT=8000

# authorization
AUTH_TOKEN=9a2ad0688a410fd29f94ef31d45d56b624358c17

# settings
INPUTFOLDER=test/examples/input
DATASET_NAME='test'
PACKAGE_NAME="testing.$DATASET_NAME.`date +"%Y%m%d-%H%M"`"
FILE_PATH="$INPUTFOLDER/$DATASET_NAME.csv"

# example title and description
TITLE='Test data set'
read -r -d '' DESCRIPTION << EOM
Test data set description
EOM

# contact information
CONTACT='Contact person'
PUBLISHER='Publishing organization'
CONTACT_EMAIL='contact@email.com'
LANGUAGE='English'

# get filename and filename without extension
FILENAME=${FILE_PATH/$INPUTFOLDER\//}
FILENAME_WO_EXT=${FILENAME/.csv/}
echo "Filename without extension: $FILENAME_WO_EXT"

REPRESENTATION_UUID=$(cat /proc/sys/kernel/random/uuid)

read -r -d '' METADATA << EOM
{
    "title": "$TITLE",
    "description": "$DESCRIPTION",
    "contactPoint": "$CONTACT",
    "contactEmail": "$CONTACT_EMAIL",
    "publisher": "$PUBLISHER",
    "publisherEmail": "$CONTACT_EMAIL",
    "language": "$LANGUAGE",
    "representations": {
        "$REPRESENTATION_UUID": {
            "distribution_label": "csv",
            "distribution_description": "CSV file",
            "access_rights": "free"
        }
    }
}
EOM

. highlight.sh

echo_highlight_header $HEADER 'register data set'
RESPONSE=`curl -H "Authorization: Token $AUTH_TOKEN" -X POST -d "package_name=$PACKAGE_NAME&basic_metadata=$METADATA" http://$SERVER:$PORT/earkweb/api/informationpackages/`
echo $RESPONSE
PROCESS_ID=`echo $RESPONSE | jq -r '.process_id'`
if [ -z "$PROCESS_ID" ]; then echo_highlight $FAIL "No process ID"; fi
echo_highlight $OKGREEN "Process ID: $PROCESS_ID"


echo_highlight_header $HEADER 'upload 1st representation'
if [ ! -f "$FILE_PATH" ]; then echo_highlight $FAIL "File not found at: $FILE_PATH"; exit 1; fi
RESPONSE=`curl  -H "Authorization: Token $AUTH_TOKEN" -F "file=@$FILE_PATH" http://$SERVER:$PORT/earkweb/api/informationpackages/$PROCESS_ID/$REPRESENTATION_UUID/data/upload/`
echo $RESPONSE
REPRESENTATION_ID1=`echo $RESPONSE  | jq -r '.representationId'`
echo_highlight $OKGREEN "Representation ID: $REPRESENTATION_ID1"

echo_highlight_header $HEADER 'create metadata file'

METADATA_FILE=/tmp/metadata.json
echo $METADATA
echo $METADATA > $METADATA_FILE
if [ -z "$METADATA_FILE" ]; then echo_highlight $FAIL "No metadata file"; fi
echo_highlight $OKGREEN "Metadata file: $METADATA_FILE"

echo_highlight_header $HEADER 'upload metadata'
RESPONSE=`curl -H "Authorization: Token $AUTH_TOKEN" --write-out %{http_code} --silent --output /dev/null -F "file=@${METADATA_FILE}" http://localhost:8000/earkweb/api/informationpackages/$PROCESS_ID/metadata/upload/`
if [ -z "$RESPONSE" ]; then echo_highlight $FAIL "No response for metadata upload request"; exit 1; fi
if [ $RESPONSE == 201 ]; then
  echo_highlight $OKGREEN "Metadata upload executed successfully with status code: $RESPONSE"
else
  echo_highlight $FAIL "Metadata upload failed with status code: $RESPONSE"
fi

echo_highlight $OKGREEN "Ingest completed"
