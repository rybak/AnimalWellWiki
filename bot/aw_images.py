#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This bot automatically cleans up file pages for images.

Parameters:

-summary        Extra message to add to the edit summary.

Example:

    python3 pwb.py aw_images '-summary:extra message'
"""

#
# © Andrei Rybak, 2019-2024
# Written for Animal Well Wiki
#
# Distributed under the terms of the MIT license.
#
# Usage:
#     1. Install pywikibot (see URL below).
#     2. Generate user-config.py for your account.
#     3. Put awwiki_family.py into directory 'pywikibot/families/'.
#        You can also generate family file yourself using script
#        'generate_family_file.py' provided in Pywikibot installation.
#     4. Put this script into 'scripts/userscripts/' directory.
#     5. Run bot with command:
#
#          python pwb.py aw_images
#
# https://support.wiki.gg/wiki/Pywikibot
#
# https://www.mediawiki.org/wiki/Manual:Pywikibot/Installation
# For more info about Pywikibot usage see
# https://www.mediawiki.org/wiki/Manual:Pywikibot/Use_on_third-party_wikis
#

from __future__ import absolute_import, division, unicode_literals

import sys
import re
from textwrap import dedent
import requests

import pywikibot
from pywikibot.pagegenerators import AllpagesPageGenerator
from pywikibot import exceptions
from pywikibot.bot_choice import QuitKeyboardInterrupt
from pywikibot.textlib import getCategoryLinks
from pywikibot.textlib import extract_sections


DEBUG = False
BOT_TASK_AD = ' ([[User:AndrybakBot/Image copyright]])'
# https://www.mediawiki.org/wiki/Manual:Namespace
FILE_NAMESPACE_ID = 6
ROOT_URL = 'https://animalwell.wiki.gg'


def put_text(page, new, summary, count, asynchronous=False):
    """
    Save the new text. Boilerplate copied from scripts/add_text.py.

    © Pywikibot team, 2013-2019
    """
    page.text = new
    try:
        page.save(summary=summary, asynchronous=asynchronous,
                  minor=page.namespace() != 3)
    except pywikibot.exceptions.EditConflictError:
        pywikibot.output('Edit conflict! skip!')
    except pywikibot.exceptions.ServerError:
        if count <= config.max_retries:
            pywikibot.output('Server Error! Wait..')
            pywikibot.sleep(config.retry_wait)
            return None
        else:
            raise pywikibot.ServerError(
                'Server Error! Maximum retries exceeded')
    except exceptions.SpamblacklistError as e:
        pywikibot.output(
            'Cannot change {} because of blacklist entry {}'
            .format(page.title(), e.url))
    except exceptions.LockedPageError:
        pywikibot.output('Skipping {} (locked page)'.format(page.title()))
    except exceptions.PageSaveRelatedError as error:
        pywikibot.output('Error putting page: {}'.format(error.args))
    else:
        return True
    return False


LOCATION_REGEX = re.compile('[lL]ocation([.]| of)?')


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """

    local_args = pywikibot.handle_args(args)

    # default values for options
    extra_summary = None

    for arg in local_args:
        option, sep, value = arg.partition(':')
        if option == '-summary':
            extra_summary = value
        else:
            pywikibot.warning("Unrecognized option {}".format(option))


    def check_option(option, value):
        if not value:
            pywikibot.error("Missing argument for option '{}'".format(option))
            return False
        return True


    templates_ready = ['Copyright game', 'CC0', 'CC-BY-SA-3.0', 'Copyright missing', 'Delete']
    site = pywikibot.Site()
    looked_at = set()
    # https://animalwell.wiki.gg/api.php?action=query&list=allpages&apnamespace=6
    # https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.pagegenerators.html#pagegenerators.AllpagesPageGenerator
    for page in AllpagesPageGenerator(namespace=FILE_NAMESPACE_ID):
        if page.title() in looked_at:
            pywikibot.output("Done.")
            break
        else:
            looked_at.add(page.title())
        try:
            page_title = page.title()
            click_url = ROOT_URL + '/wiki/' + page.title(underscore=True)
            pywikibot.output("Page '{0}' | {1}".format(page_title, click_url))
            ts = page.templatesWithParams()
            if len(ts) > 0:
                found_ready = False
                for t in ts:
                    for r in templates_ready:
                        if r in t[0].title():
                            pywikibot.output("Page <<lightgreen>>{0}<<default>> has template: {1}".format(page_title, t[0]))
                            found_ready = True
                            break
                if found_ready:
                    pywikibot.output("\tSkipping.")
                    continue

            old_text = page.get()
            # categories = getCategoryLinks(old_text, site)
            # categories_text = '\n'.join(map(lambda c:c.aslink(), categories))
            (header, body, footer) = extract_sections(old_text, site)
            summary = None
            licensing = None
            description = None
            for section in body:
                if 'ummary' in section[0] or 'escription' in section[0]:
                    summary = section[1]
                if 'icens' in section[0]:
                    licensing = section[1]
            got_summary_from_header = False
            if summary is None:
                got_summary_from_header = True
                summary = header

            new_text = None
            pywikibot.output("Editing page <<lightblue>>{0}<<default>>.".format(page_title))
            if summary is not None and len(summary.strip()) > 0:
                summary = summary.strip()
                pywikibot.output("Have \"Summary\":\n\t{}".format(summary))
                i = summary.find('{')
                if i > 0:
                    summary = summary[0:i]
                i = summary.find(' in ')
                if i > 0:
                    summary = summary[0:i]
                summary = summary.strip()
                if summary[-1] == '.':
                    summary = summary[0:-1]

                # Lots of images have descriptions like 'Brick Egg2', but we just want the 'Brick Egg' portion.
                if '2' in summary:
                    summary = summary.replace('2', '')
                # if the word "location" is mentioned, we want to wikilink the other word
                if 'ocation' in summary:
                    maybe_page = LOCATION_REGEX.sub(string=summary, repl='').strip().capitalize()
                    summary = 'Location of [[' + maybe_page + ']].'
                elif 'Egg' in summary:
                    summary = '[[' + summary + ']]'

                pywikibot.output("Will have \"Summary\" section:\n\t{}".format(summary))
                choice = pywikibot.input_choice("Is it a good summary?",
                    [('Yes', 'y'), ('No', 'n'), ('open in Browser', 'b')], 'n')
                if choice == 'y':
                    description = summary
                elif choice == 'n':
                    pass
                elif choice == 'b':
                    pywikibot.bot.open_webbrowser(page)
            if description is None:
                pywikibot.output("Type '[s]kip' to skip the image completely.")
                description = pywikibot.input("Please describe the file:")
                if description in ['s', 'skip']:
                    continue
            if licensing is not None:
                pywikibot.output("Have \"Licensing\":\n\t{}".format(licensing.strip()))

            new_text = dedent("""
                == Summary ==
                {0}

                == Licensing ==
                {{{{Copyright game}}}}
                """.format(description)).strip()
            header = header.strip()
            if not got_summary_from_header and len(header) > 0:
                new_text = header + '\n\n' + new_text
            footer = footer.strip()
            if len(footer) > 0:
                new_text += '\n\n' + footer

            # check if the edit is sensible
            if old_text == new_text:
                pywikibot.output("No changes. Nothing to do.")
                continue
            # report what will happen
            pywikibot.showDiff(old_text, new_text, context=3)

            base_summary = "add [[Template:Copyright game]]" + BOT_TASK_AD
            edit_summary = f"{base_summary} ({extra_summary})" if extra_summary else base_summary

            pywikibot.output("Edit summary will be\n\t<<lightblue>>{0}<<default>>".format(edit_summary))
            choice = pywikibot.input_choice(
                "Do you want to accept these changes?",
                [('Yes', 'y'), ('No', 'n'), ('open in Browser', 'b')], 'n')

            # uncomment when testing
            # if choice == 'y':
            #     pywikibot.output("Test run, doing nothing.")
            #     continue

            if choice == 'n':
                pywikibot.output("Okay, doing nothing.")
                continue
            elif choice == 'b':
                pywikibot.bot.open_webbrowser(page)
            elif choice == 'y':
                error_count = 0
                while True:
                    result = put_text(page, new_text, edit_summary, error_count)
                    if result is not None:
                        pywikibot.output("Got result of saving: {}".format(result))
                        break
                    error_count += 1
                continue
            elif choice == 'q':
                break

        # https://doc.wikimedia.org/pywikibot/master/api_ref/exceptions.html#exceptions.NoPageError
        except exceptions.NoPageError:
            pywikibot.error("{} doesn't exist, skipping.".format(page.title()))
            continue
        except exceptions.IsRedirectPageError:
            pywikibot.error("{} is a redirect, skipping".format(page.title()))
            continue
        except exceptions.Error as e:
            pywikibot.bot.suggest_help(exception=e)
            continue
        except QuitKeyboardInterrupt:
            sys.exit("User quit bot run.")
        else:
            pass


if __name__ == '__main__':
    main()
