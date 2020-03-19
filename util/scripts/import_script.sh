#!/bin/bash

DEST=http://localhost:8000/earkweb/
CAS_HOSTNAME=earkwebdev.ait.ac.at:8443
CAS_USERNAME=
CAS_PASSWORD=
MYSQL_USERNAME=
MYSQL_PASSWORD=

# Where headers and cookies should be saved
COOKIE_JAR=.cookieJar
HEADER_DUMP_DEST=.headers

# Start by logging out 
curl -s -k https://earkwebdev.ait.ac.at:8443/cas/logout -o /dev/null

#Cleanup existing coockie and header
rm $COOKIE_JAR
rm $HEADER_DUMP_DEST

#Encode destination
ENCODED_DEST=`echo "$DEST" | perl -p -e 's/([^A-Za-z0-9])/sprintf("%%%02X", ord($1))/seg' | sed 's/%2E/./g' | sed 's/%0A//g'`

# Get CAS id
CAS_ID=`curl -s -k -c $COOKIE_JAR https://earkwebdev.ait.ac.at:8443/cas/login?service=$ENCODED_DEST | grep name=.lt | sed 's/.*value..//' | sed 's/\".*//'`
echo "CAS_ID=$CAS_ID"

# Get headers
curl -s -k --data "username=$CAS_USERNAME&password=$CAS_PASSWORD&lt=$CAS_ID&execution=e1s1&_eventId=submit" -i -b $COOKIE_JAR -c $COOKIE_JAR https://$CAS_HOSTNAME/cas/login?service=$ENCODED_DEST -D $HEADER_DUMP_DEST -o /dev/null
cat ./.headers

# Get the location from headers
CURL_DEST=`grep Location $HEADER_DUMP_DEST | sed 's/Location: //'`
echo "CURL_DEST=$CURL_DEST"

# Get ticket
TICKET=`echo $CURL_DEST | awk -F ticket= '{ print $2 }'`
echo "TICKET=$TICKET"

# Encode ticket
ENCODED_TICKET=`echo "ticket=$TICKET" | perl -p -e 's/([^A-Za-z0-9])/sprintf("%%%02X", ord($1))/seg' | sed 's/%2E/./g' | sed 's/%0A//g'`
echo "ENCODED_TICKET=$ENCODED_TICKET"

# Build URl for a get request
GET_DEST="$DEST?$ENCODED_TICKET"
echo "GET_DEST=$GET_DEST"

# Issue a GET first (do not remove is necessary)
GET_RESULT=`curl -s -k -L -b $COOKIE_JAR -c $COOKIE_JAR $GET_DEST`
#echo "GET_RESULT=$GET_RESULT"

# Build URL for POST request
POST_DEST="$DEST/?$ENCODED_TICKET"
echo "POST_DEST=$POST_DEST"

#POST_RESULT=`curl -s -X POST -k -L -b $COOKIE_JAR -c $COOKIE_JAR "$DEST?$ENCODED_TICKET&pkg_id=28f07c7c-ad73-4113-81c3-59534c4f6f9b"`
DEST=http://localhost:8000/earkweb/search/order_status
POST_RESULT=`curl -s -X POST -k -L --data "pkg_uuid=28f07c7c-ad73-4113-81c3-59534c4f6f9b" -b $COOKIE_JAR -c $COOKIE_JAR "$DEST/?$ENCODED_TICKET"`
echo "$POST_RESULT" > result.html
cat ./result.html

# Build URl for a get request
DEST=http://localhost:8000/earkweb/submission/initialize/test_pack3
GET_RESULT=`curl -s -X GET -k -L -b $COOKIE_JAR -c $COOKIE_JAR "$DEST?$ENCODED_TICKET"`
echo "$GET_RESULT" > result.html
cat ./result.html

SIP_ID=$GET_RESULT

# Add one representation
DEST=http://localhost:8000/earkweb/submission/add_representation
GET_RESULT=`curl -s -X POST -k -L --data "representation=rep_001" -b $COOKIE_JAR -c $COOKIE_JAR "$DEST/$SIP_ID/?$ENCODED_TICKET"`
echo "$GET_RESULT" > result.html
cat ./result.html

# Find test_pack3 and get process_id
DEST=http://localhost:8000/earkweb/submission/process_id
GET_RESULT=`curl -s -X GET -k -L -b $COOKIE_JAR -c $COOKIE_JAR "$DEST/$SIP_ID/?$ENCODED_TICKET"`
echo "$GET_RESULT" > result.html
cat ./result.html

SIP_UUID=$GET_RESULT

# Add files to representation
DEST=http://localhost:8000/earkweb/submission/ins_file
GET_RESULT=`curl  --form "rep=rep_001" --form "subdir=data" --form "content_file=@./result.html"  -H "Content-Type: multipart/form-data" -k -L -b $COOKIE_JAR -c $COOKIE_JAR "$DEST/$SIP_UUID/representations?$ENCODED_TICKET"`
#-F file=@./result.html
echo "$GET_RESULT" > result.html
cat ./result.html

# Execute celery tasks
PYSCRIPT=$"from config.configuration import config_path_work
from taskbackend.tasks import SIPReset
from taskbackend.tasks import SIPDescriptiveMetadataValidation
from taskbackend.tasks import SIPPackageMetadataCreation
from taskbackend.tasks import SIPPackaging
from taskbackend.tasks import SIPClose
from taskbackend.default_task_context import DefaultTaskContext
task_context = DefaultTaskContext('$SIP_UUID', \"%s/$SIP_UUID\" % config_path_work, 'SIPReset', None, {}, None)
SIPReset().apply((task_context,), queue='default').status
SIPDescriptiveMetadataValidation().apply((task_context,), queue='default').status
SIPPackageMetadataCreation().apply((task_context,), queue='default').status
SIPPackaging().apply((task_context,), queue='default').status
SIPClose().apply((task_context,), queue='default').status"

echo "$PYSCRIPT" | python manage.py shell

# Update status in DB
echo "update informationpackage set last_task_id=\"SIPClose\" where process_id=\"$SIP_UUID\";" | mysql -u $MYSQL_USERNAME -p$MYSQL_PASSWORD earkweb
