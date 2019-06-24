#!/usr/bin/env bash

if [ ! $# -eq 1 ]; then
	echo "Usage upload.sh <filename>"
	exit 1
fi

echo $1

./preproc.py "$1" | curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $ARCHIVE_SERVICE_TOKEN" "http://127.0.0.1:5000/api/add" -d @-
