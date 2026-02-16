#!/bin/bash

echo 'Hello World'
echo 'Hello Worlds'
echo "today is a good day"
date
FILE='file'
echo "The file name is ${FILE}.xml and the file name is ${FILE}.json"

echo 'The file name is ${FILE}.xml and the file name is ${FILE}.json'
date
TODAT=$(date +%Y-%m-%d)
echo "today is ${TODAT}"
CURRENT_USER=$(whoami)

echo "Current user is ${CURRENT_USER}"

FILE=$1
LINES=$(wc --lines < $FILE)
echo "The file ${FILE} has ${LINES} lines"
echo "all the files: $@"
echo "all the files: $#"

DEFAULT_FILE=${1:-default.txt}
echo "The file name is ${DEFAULT_FILE}"