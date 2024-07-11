#!/bin/bash

read_db() {
  sqlite3 "$1" ".dump" > "$1.sql"
}

if [ -f "$1" ]; then
  extension="${1##*.}"
  if [ "$extension" == "db" ]; then
    read_db "$1"
  fi
fi
