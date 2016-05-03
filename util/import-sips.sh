#!/bin/bash
DATA_DIR=./
for f in $DATA_DIR/*.zip
	do python ./import-sip.py -f $f
done
