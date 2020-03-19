#!/bin/bash
DEST=http://earkwebdev.ait.ac.at/earkweb/search/order_status
#DEST=http://localhost:8000/earkweb/search/order_status
CAS_HOSTNAME=https://earkwebdev.ait.ac.at:8443
USERNAME=eark
PASSWORD=eark
COOKIE_JAR=.cookieJar
HEADER_DUMP_DEST=.headers

# Start by logging out 
curl -s -k $CAS_HOSTNAME/cas/logout -o /dev/null

#Cleanup existing coockie and header
rm $COOKIE_JAR
rm $HEADER_DUMP_DEST

#Encode destination
ENCODED_DEST=`echo "$DEST" | perl -p -e 's/([^A-Za-z0-9])/sprintf("%%%02X", ord($1))/seg' | sed 's/%2E/./g' | sed 's/%0A//g'`

echo "---------------------------------------------------"
echo "getting CAS_ID"
#Visit CAS and get a login form. This includes a unique ID for the form, which we will store in CAS_ID and attach to our form submission. jsessionid cookie will be set here
CAS_ID=`curl -s -k -c $COOKIE_JAR https://earkwebdev.ait.ac.at:8443/cas/login?service=$ENCODED_DEST | grep name=.lt | sed 's/.*value..//' | sed 's/\".*//'`
cat $COOKIE_JAR
echo "CAS_ID=$CAS_ID"
if [[ "$CAS_ID" = "" ]]; then
   echo "Login ticket is empty."
   exit 1
fi

echo "---------------------------------------------------"
sleep 2

echo "Logging in"
#Submit the login form, using the cookies saved in the cookie jar and the form submission ID just extracted. We keep the headers from this request as the return value should be a 302 including a "ticket" param which we'll need in the next request

curl -s -k --data "username=$USERNAME&password=$PASSWORD&lt=$CAS_ID&execution=e1s1&_eventId=submit" -i -b $COOKIE_JAR -c $COOKIE_JAR $CAS_HOSTNAME/cas/login?service=$ENCODED_DEST -D $HEADER_DUMP_DEST -o /dev/null
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

# Visit the URL with the ticket param to finally set the casprivacy and, more importantly, MOD_AUTH_CAS cookie. Now we've got a MOD_AUTH_CAS cookie, anything we do in this session will pass straight through CAS
GET_RESULT=`curl -s -k -L -b $COOKIE_JAR -c $COOKIE_JAR $GET_DEST`
echo "GET_RESULT=$GET_RESULT"

# Build URL for POST request
POST_DEST="$DEST/?$ENCODED_TICKET"
echo "POST_DEST=$POST_DEST"

# Issue POST or GET request
#POST_RESULT=`curl -s -X POST -k -L --data "asdfafda" -b $COOKIE_JAR -c $COOKIE_JAR $POST_DEST`
#POST_RESULT=`curl -s -X POST -k -L --data @./earkweb/xml/resources/order.xml -b $COOKIE_JAR -c $COOKIE_JAR $POST_DEST`
#echo "POST_RESULT=$POST_RESULT"
#echo "$POST_RESULT" > result.html
PKG_UUID="20ce1828-8890-439c-9827-b237d5162b90"
#POST_RESULT=`curl -s -X POST -k -L -b $COOKIE_JAR -c $COOKIE_JAR "$DEST?$ENCODED_TICKET&pkg_id=28f07c7c-ad73-4113-81c3-59534c4f6f9b"`
POST_RESULT=`curl -s -X POST -k -L --data "pkg_uuid=$PKG_UUID" -b $COOKIE_JAR -c $COOKIE_JAR "$DEST/?$ENCODED_TICKET"`
echo "$POST_RESULT" > result.html

#cat ./result.html

