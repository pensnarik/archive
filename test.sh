#!/usr/bin/env bash

if [ ! $# -eq 1 ]; then
	echo "Usage test.sh <path>"
	exit 1
fi

OIFS="$IFS"
IFS=$'\n'

for file in $(find "$1" -type f); do
	./upload.sh "$file"
done

IFS="$OIFS"