#!/bin/bash

DEST=http://localhost:8000/earkweb/
MYSQL_USERNAME=repo
MYSQL_PASSWORD=repo

# Build URl for a get request
GET_DEST="$DEST"
echo "GET_DEST=$GET_DEST"

# Issue a GET first (do not remove is necessary)
GET_RESULT=`curl -s -k -L $GET_DEST`
echo "GET_RESULT=$GET_RESULT"

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
