#!/bin/sh

if [ ! -z "$1" ]; then SCHEMA=$1; else SCHEMA="gar"; fi

sh ./download_shemas.sh ${SCHEMA}
rc=$?
if [ $rc -eq 0 ]; 
then
  DATE=$(date '+%Y-%m-%d')
  OUTPUT="${SCHEMA}-${DATE}.sql"
  python main.py schemas/${SCHEMA} output/ --sql-syntax=pgsql --xsd-schema=${SCHEMA} --no-data --join=${OUTPUT}
  rc=$?
  if [ $rc -eq 0 ]; then
    echo "------\nSuccess done. Result file: "
    ls -l "output/${OUTPUT}"
  fi
else 
  exit 1
fi