#!/bin/bash

source config.sh

set -u
filename="$SCRIPT_FILENAME"
SRC="${BOT_LOCATION}/scripts/userscripts"
DEST="."

source overwrite.sh
