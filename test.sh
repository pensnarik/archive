#!/usr/bin/env bash

if [ ! $# -eq 1 ]; then
	echo "Usage test.sh <path>"
	exit 1
fi

OIFS="$IFS"
IFS=$'\n'

for file in $(find "$1" -type f); do
	echo "$file"
	./preproc.py "$file" | curl -X POST -H "Content-Type: application/json" "http://127.0.0.1:5000/api/add" -d @-
done

IFS="$OIFS"