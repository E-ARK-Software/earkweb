#!/usr/bin/env bash
echo "DIP PREPARE"
RESP=`curl -s -X POST -d '{"process_id": "c1b1c16e-2c00-474f-b99b-42019b3eaeed"}' http://localhost:8000/earkweb/search/prepareDIPWorkingArea`
echo $RESP

JOBID=`echo $RESP | awk -F"," '{print $4}' | awk -F":" '{print $2}' | sed 's/ //g;s/\}//g;s/\"//g'`
for i in {1..9}; do
    echo `curl -s http://localhost:8000/earkweb/search/jobstatus/$JOBID`
    sleep 2
done

#sleep 1
#echo `curl -s http://localhost:8000/earkweb/search/jobstatus/$JOBID`
#
#sleep 5
#
#echo "DIP CREATE"
#RESP2=`curl -s -X POST -d '{"process_id": "c1b1c16e-2c00-474f-b99b-42019b3eaeed"}' http://localhost:8000/earkweb/search/createDIP`
#echo $RESP2
#
#JOBID2=`echo $RESP2 | awk -F"," '{print $4}' | awk -F":" '{print $2}' | sed 's/ //g;s/\}//g;s/\"//g'`
#echo $JOBID2
#echo `curl -s http://localhost:8000/earkweb/search/jobstatus/$JOBID2`
#sleep 1
#echo `curl -s http://localhost:8000/earkweb/search/jobstatus/$JOBID2`
