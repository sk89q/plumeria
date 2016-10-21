"""Add ifttt integration so users can call their own ifttt hooks."""

import json
import re
from json import JSONDecodeError

import CommonMark

from plumeria.command import commands, CommandError
from plumeria.message import Message
from plumeria.middleware.user_prefs import prefs_manager
from plumeria.perms import direct_only
from plumeria.util import http
from plumeria.util.message import strip_html
from plumeria.util.ratelimit import rate_limit

EVENT_NAME_RE = re.compile("^[A-Za-z0-9_\\- ]{1,40}$")
VALID_MAKER_KEY_RE = re.compile("^[A-Za-z0-9_\\- ]{1,70}$")


def valid_maker_key(s):
    if not VALID_MAKER_KEY_RE.search(s):
        raise ValueError("Invalid ifttt Maker key")
    return s


maker_key = prefs_manager.create("ifttt_maker_key", type=valid_maker_key, fallback=None, comment="Your ifttt Maker key",
                                 private=True)


@commands.create("ifttt", ".", category="Utility")
@rate_limit()
@direct_only
async def ifttt_maker(message: Message):
    """
    Fire a ifttt Maker event.

    You can trigger ifttt recipes using this command. Create recipes first
    using the `Maker Channel <https://ifttt.com/maker>`_ and then add your Maker
    key using the :code:`/pset ifttt_maker_key your_key` command.

    Here's how you could trigger an email event::

        /ifttt email

    Regarding variables: Value1 refers to the raw input data, Value2 refers to an HTML
    version, and Value3 is a Markdown and HTML free version.

    """
    parts = message.content.strip().split(" ", 1)
    if len(parts) == 1:
        event_name, data = parts[0], ""
    else:
        event_name, data = parts

    if not EVENT_NAME_RE.search(event_name):
        raise CommandError("Invalid event name. Only alphanumeric, dash, space, and underscore letters are allowed.")

    try:
        key = await prefs_manager.get(maker_key, message.author)
    except KeyError:
        raise CommandError("Set your Maker key with /pset ifttt_maker_key your_key first.")

    html = CommonMark.commonmark(data)
    text = strip_html(html)

    r = await http.post("https://maker.ifttt.com/trigger/{}/with/key/{}".format(event_name, key), data=json.dumps({
        "value1": data,
        "value2": html,
        "value3": text,
    }), headers=(('Content-Type', 'application/json'),), require_success=False)

    try:
        response = r.json()
        if 'errors' in response:
            raise CommandError("ifttt says: " + "\n".join([error['message'] for error in response['errors']]))
    except JSONDecodeError:
        pass

    return r.text()

def setup():
    prefs_manager.add(maker_key)
    commands.add(ifttt_maker)
