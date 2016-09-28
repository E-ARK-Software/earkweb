LOGIN_URL=http://localhost:8000/earkweb/admin/login/
YOUR_USER=''
YOUR_PASS=''
COOKIES=cookies.txt
CURL_BIN="curl -s -c $COOKIES -b $COOKIES -e $LOGIN_URL"

#echo -n "Django Auth: get csrftoken ..."
$CURL_BIN $LOGIN_URL > /dev/null
DJANGO_TOKEN="csrfmiddlewaretoken=$(grep csrftoken $COOKIES | sed 's/^.*csrftoken\s*//')"

#echo -n " perform login ..."
$CURL_BIN \
    -d "$DJANGO_TOKEN&username=$YOUR_USER&password=$YOUR_PASS" \
    -X POST $LOGIN_URL

#echo $DJANGO_TOKEN

#echo -n " do something while logged in ..."
$CURL_BIN \
    -b $DJANGO_TOKEN \
    -d	"{\"order_title\":\"example title_1\",\"aip_identifiers\":[\"b7738768-032d-3db1-eb42-b09611e6e6c6\",\"916c659c-909d-ad94-2289-c7ee8e7482d9\"]}" \
    -X POST http://localhost:8000/earkweb/search/submit_order/

#echo " logout"
rm $COOKIES
