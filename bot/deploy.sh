#!/bin/bash

source config.sh

set -u
filename="$SCRIPT_FILENAME"
DEST="${BOT_LOCATION}/scripts/userscripts"
SRC="."

source overwrite.sh

ls -l "$DEST"
