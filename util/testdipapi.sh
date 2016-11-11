#!/usr/bin/env bash

QITER=10
PAUSE=2

echo "DIP PREPARE"

# fd6b2828-7a51-42fe-954e-47db66102bf9
# c1b1c16e-2c00-474f-b99b-42019b3eaeed
RESP=`curl -s -X POST -d '{"process_id": "a4bc91db-70d1-4eb0-816d-aaf7beb7b8cd"}' http://localhost:8000/earkweb/search/prepareDIPWorkingArea`
echo $RESP

# status
JOBID=`echo $RESP | awk -F"," '{print $4}' | awk -F":" '{print $2}' | sed 's/ //g;s/\}//g;s/\"//g'`
for i in {1..$QITER}; do
    echo `curl -s http://localhost:8000/earkweb/search/jobstatus/$JOBID`
    sleep $PAUSE
done

#sleep $PAUSE
#echo `curl -s http://localhost:8000/earkweb/search/jobstatus/$JOBID`


echo "DIP CREATE"

RESP2=`curl -s -X POST -d '{"process_id": "a4bc91db-70d1-4eb0-816d-aaf7beb7b8cd"}' http://localhost:8000/earkweb/search/createDIP`
echo $RESP2
# status
sleep 3
JOBID2=`echo $RESP2 | awk -F"," '{print $4}' | awk -F":" '{print $2}' | sed 's/ //g;s/\}//g;s/\"//g'`


for i in {1..$QITER}; do
    echo `curl -s http://localhost:8000/earkweb/search/jobstatus/$JOBID2`
    sleep $PAUSE
done

#sleep $PAUSE
#echo `curl -s http://localhost:8000/earkweb/search/jobstatus/$JOBID2`
