#!/usr/bin/env bash

if [ ! $# -eq 1 ]; then
	echo "Usage test.sh <path>"
	exit 1
fi

OIFS="$IFS"
IFS=$'\n'

for file in $(find "$1" -not -wholename "*.git/*" -name "*.jpg" -type f); do
	./upload.sh "$file"
	./backup.py "google" "$file"
done

IFS="$OIFS"