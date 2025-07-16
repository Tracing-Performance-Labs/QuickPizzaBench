#!/bin/bash

CONFIG="$1"

if [ -z "$CONFIG" ]; then
  echo '$CONFIG is not set' >&2;
  exit 1;
fi

FILENAME="$(date +"%d%m%y")-quickpizza-$CONFIG-20vus-60s-t3.medium.gz"

echo "Saving benchmark results to: $FILENAME"

k6 run --out csv="$FILENAME" k6-quickpizza.js
