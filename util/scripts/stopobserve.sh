#!/usr/bin/env bash
pid=`ps aux|grep -e observe.*\.py |grep -v color|awk '{print $2}'`
kill -9 $pid