#!/bin/sh

# This is the Python command required to run the Animal Well Wiki bot script
# 'aw_images.py'.  For available options, see file 'bot/aw_images.py'.
#
# Make sure the bot is deployed to PWB dir before running.

# the configuration file shall provide $BOT_LOCATION, $SCRIPT_NAME, and
# SCRIPT_FILENAME=aw_images
. $(dirname $0)/bot/config.sh

# Move to the checkout dir of pywikibot's core (stable branch is recommended)
cd "$(dirname $0)/bot/$BOT_LOCATION"

# Execute the bot script $SCRIPT_NAME with all given CLI arguments
# see https://support.wiki.gg/wiki/Pywikibot for more info
exec python pwb.py $SCRIPT_NAME "${@}"
