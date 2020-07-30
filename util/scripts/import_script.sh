#!/usr/bin/env bash
# required: libreoffice, jq, highlight.sh


# server
SERVER=localhost
PORT=8000

# settings
INPUTFOLDER=test/examples/input
DATASET_NAME='test'
PACKAGE_NAME="testing.$DATASET_NAME.202007301809"
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

. highlight.sh

echo_highlight_header $HEADER 'register data set'
RESPONSE=`curl -H 'Authorization: Token 9a2ad0688a410fd29f94ef31d45d56b624358c17' -X POST -d "package_name=$PACKAGE_NAME" http://$SERVER:$PORT/earkweb/api/informationpackages/`
echo $RESPONSE
PROCESS_ID=`echo $RESPONSE | jq -r '.process_id'`
if [ -z "$PROCESS_ID" ]; then echo_highlight $FAIL "No process ID"; fi
echo_highlight $OKGREEN "Process ID: $PROCESS_ID"


echo_highlight_header $HEADER 'upload 1st representation'
if [ ! -f "$FILE_PATH" ]; then echo_highlight $FAIL "File not found at: $FILE_PATH"; exit 1; fi
RESPONSE=`curl  -H 'Authorization: Token 9a2ad0688a410fd29f94ef31d45d56b624358c17' -F "file=@$FILE_PATH" http://$SERVER:$PORT/earkweb/api/informationpackages/$PROCESS_ID/data/upload/`
echo $RESPONSE
REPRESENTATION_ID1=`echo $RESPONSE  | jq -r '.representationId'`
echo_highlight $OKGREEN "Representation ID: $REPRESENTATION_ID1"

#echo_highlight_header $HEADER 'convert to ods'
#libreoffice --headless --convert-to ods $FILE_PATH --outdir $INPUTFOLDER
#FILE_CONVERTED="${INPUTFOLDER}/${FILENAME_WO_EXT}.ods"
#if [ ! -f "$FILE_CONVERTED" ]; then echo_highlight $FAIL "Converted file not found at: $FILE_CONVERTED"; exit 1; fi
#echo_highlight $OKGREEN "Converted file: $FILE_CONVERTED"

echo_highlight_header $HEADER 'Using existing ODS file'
ODS_FILE="${INPUTFOLDER}/${FILENAME_WO_EXT}.ods"
if [ ! -f "$ODS_FILE" ]; then echo_highlight $FAIL "Converted file not found at: $ODS_FILE"; exit 1; fi
echo_highlight $OKGREEN "ODS file: $ODS_FILE"

echo_highlight_header $HEADER 'upload 2nd representation'
RESPONSE=`curl -H 'Authorization: Token 9a2ad0688a410fd29f94ef31d45d56b624358c17' -F "file=@$INPUTFOLDER/${FILENAME_WO_EXT}.ods" http://$SERVER:$PORT/earkweb/api/informationpackages/$PROCESS_ID/data/upload/`
echo $RESPONSE
REPRESENTATION_ID2=`echo $RESPONSE | jq -r '.representationId'`
if [ -z "$REPRESENTATION_ID2" ]; then echo_highlight $FAIL "No representation ID for 1st file"; fi
echo_highlight $OKGREEN "Representation ID: $REPRESENTATION_ID2"

echo_highlight_header $HEADER 'create metadata file'
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
        "$REPRESENTATION_ID1": {
            "distribution_label": "csv",
            "distribution_description": "CSV file",
            "access_rights": "free"
        },
        "$REPRESENTATION_ID2": {
            "distribution_label": "ods",
            "distribution_description": "Open Document Spreadsheet file",
            "access_rights": "free"
        }
    }
}
EOM
METADATA_FILE=/tmp/metadata.json
echo $METADATA
echo $METADATA > $METADATA_FILE
if [ -z "$METADATA_FILE" ]; then echo_highlight $FAIL "No metadata file"; fi
echo_highlight $OKGREEN "Metadata file: $METADATA_FILE"

echo_highlight_header $HEADER 'upload metadata'
RESPONSE=`curl -H 'Authorization: Token 9a2ad0688a410fd29f94ef31d45d56b624358c17' --write-out %{http_code} --silent --output /dev/null -F "file=@${METADATA_FILE}" http://localhost:8000/earkweb/api/informationpackages/$PROCESS_ID/metadata/upload/`
if [ -z "$RESPONSE" ]; then echo_highlight $FAIL "No response for metadata upload request"; exit 1; fi
if [ $RESPONSE == 201 ]; then
  echo_highlight $OKGREEN "Metadata upload executed successfully with status code: $RESPONSE"
else
  echo_highlight $FAIL "Metadata upload failed with status code: $RESPONSE"
fi

