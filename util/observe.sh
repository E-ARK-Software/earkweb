#!/usr/bin/env bash

CURR_DIR=`pwd`
if [[ ! "$CURR_DIR" == *util ]]
then
    CURR_DIR="$CURR_DIR/util"
fi

python $CURR_DIR/observewatch.py &

python $CURR_DIR/observereg.py &