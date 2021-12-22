#!/bin/bash
#set -o verbose
# Usage: cas-get.sh {url} {username} {password} # If you have any errors try removing the redirects to get more information
# The service to be called, and a url-encoded version (the url encoding isn't perfect, if you're encoding complex stuff you may wish to replace with a different method)
DEST="$1"
echo $DEST
ENCODED_DEST=`echo "$DEST" | perl -p -e 's/([^A-Za-z0-9])/sprintf("%%%02X", ord($1))/seg' | sed 's/%2E/./g' | sed 's/%0A//g'`
echo "ENCODED_DEST=$ENCODED_DEST"
#IP Addresses or hostnames are fine here
CAS_HOSTNAME=$2
echo "CAS_HOSTNAME=$CAS_HOSTNAME"
#Authentication details. This script only supports username/password login, but curl can handle certificate login if required
USERNAME=$3
echo "USERNAME=$USERNAME"
PASSWORD=$4
echo "PASSWORD=$PASSWORD"

#Temporary files used by curl to store cookies and http headers
COOKIE_JAR=.cookieJar
HEADER_DUMP_DEST=.headers

rm $COOKIE_JAR
rm $HEADER_DUMP_DEST

#The script itself is below

echo "---------------------------------------------------"
echo "getting CAS_ID"
#Visit CAS and get a login form. This includes a unique ID for the form, which we will store in CAS_ID and attach to our form submission. jsessionid cookie will be set here
#CAS_ID=`curl -s -k -c ${COOKIE_JAR} https://${CAS_HOSTNAME}/cas/login?service=${ENCODED_DEST} | tee response1.txt | grep 'name=.execution\|name=.lt' | sed 's/.*value..//' | sed 's/\".*//'`
CAS_ID=`curl -s -k -c $COOKIE_JAR https://$CAS_HOSTNAME/cas/login?service=$ENCODED_DEST | grep name=.lt | sed 's/.*value..//' | sed 's/\".*//'`
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
curl -s -k --data "username=$USERNAME&password=$PASSWORD&lt=$CAS_ID&execution=e1s1&_eventId=submit" -i -b $COOKIE_JAR -c $COOKIE_JAR https://$CAS_HOSTNAME/cas/login?service=$ENCODED_DEST -D $HEADER_DUMP_DEST -o /dev/null
cat $HEADER_DUMP_DEST
echo "---------------------------------------------------"

#Linux may not need this line but my response from the previous call has retrieving windows-style linebreaks in OSX
#dos2unix $HEADER_DUMP_DEST > /dev/null

ENCODED_TICKET=`echo "$TICKET" | perl -p -e 's/([^A-Za-z0-9])/sprintf("%%%02X", ord($1))/seg' | sed 's/%2E/./g' | sed 's/%0A//g'`

#Visit the URL with the ticket param to finally set the casprivacy and, more importantly, MOD_AUTH_CAS cookie. Now we've got a MOD_AUTH_CAS cookie, anything we do in this session will pass straight through CAS
CURL_DEST=`grep Location $HEADER_DUMP_DEST | sed 's/Location: //'`
echo "CURL_DEST=$CURL_DEST"

TICKET=`echo $CURL_DEST | sed 's/ticket=//'`
echo "ticket=$TICKET"

#ENCODED_CURL_DEST=`echo "$CURL_DEST" | perl -p -e 's/([^A-Za-z0-9])/sprintf("%%%02X", ord($1))/seg' | sed 's/%2E/./g' | sed 's/%0A//g'`
#echo "ENCODED_CURL_DEST=$ENCODED_CURL_DEST"

GET_DEST="$DEST/?$ENCODED_TICKET"
echo "GET_DEST=$GET_DEST"

if [[ "$CURL_DEST" = "" ]]; then
    echo "Cannot login. Check if you can login in a browser using user/pass = $USERNAME/$PASSWORD and the following url: https://$CAS_HOSTNAME/cas/login?service=$ENCODED_DEST"
    exit 1
fi



#curl -s -k -b $COOKIE_JAR -c $COOKIE_JAR $ENCODED_CURL_DEST
curl -k -b $COOKIE_JAR -c $COOKIE_JAR $GET_DEST

#If our destination is not a GET we'll need to do a GET to, say, the user dashboard here

#Visit the place we actually wanted to go to
#curl -X POST -d 'asdfasd' -s -k -L -b $COOKIE_JAR "$DEST"
