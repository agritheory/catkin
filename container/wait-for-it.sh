#!/bin/sh
# Simple wait-for-it script to wait for a host:port to be available
HOST=${1}
PORT=${2}
TIMEOUT=${3:-30}
QUIET=${4:-0}

if [ $# -lt 2 ]; then
  echo "Usage: $0 host port [timeout] [quiet]"
  exit 1
fi

start_time=$(date +%s)
end_time=$((start_time + TIMEOUT))

if [ $QUIET -ne 1 ]; then
  echo "Waiting for $HOST:$PORT for up to $TIMEOUT seconds..."
fi

while [ $(date +%s) -lt $end_time ]; do
  nc -z $HOST $PORT > /dev/null 2>&1
  result=$?
  if [ $result -eq 0 ]; then
    if [ $QUIET -ne 1 ]; then
      echo "Connection to $HOST:$PORT succeeded!"
    fi
    exit 0
  fi
  sleep 1
done

if [ $QUIET -ne 1 ]; then
  echo "Timeout: Could not connect to $HOST:$PORT within $TIMEOUT seconds"
fi
exit 1
