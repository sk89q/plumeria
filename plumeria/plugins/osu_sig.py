import shlex
import urllib.parse
import re

from plumeria.command import commands, CommandError, ArgumentParser
from plumeria.message import Response
from plumeria.util.message import fetch_image
from plumeria.util.ratelimit import rate_limit

HEX_COLOR_PATTERN = re.compile("^#?([a-f0-9]{6})$")
USERNAME_PATTERN = re.compile("^[^/ ]+$")  # overly permissive
MODES = {'default': 0, 'taiko': 1, 'ctb': 2, 'mania': 3}


def validate_username(s):
    if USERNAME_PATTERN.match(s):
        return s
    raise CommandError("Invalid osu! username")


def validate_hex_color(s):
    m = HEX_COLOR_PATTERN.search(s)
    if m:
        return m.group(1)
    raise CommandError("Invalid hex color code")


@commands.register("osu sig", "osusig", category="Games")
@rate_limit()
async def osu_sig(message):
    """
    Gets the signature image for a osu! player. Arguments are:

    * Username
    * (optional) Mode (of default, taiko, ctb, or mania)
    * (optional) Color (in hex, like #000000)

    Example::

        /osusig username

    """
    parser = ArgumentParser()
    parser.add_argument("username", type=validate_username)
    parser.add_argument("mode", nargs='?', default="default", choices=MODES.keys())
    parser.add_argument("color", nargs='?', type=validate_hex_color, default="bb1177")
    args = parser.parse_args(shlex.split(message.content))
    url = "http://lemmmy.pw/osusig/sig.php?{}".format(urllib.parse.urlencode((
        ("uname", args.username),
        ("mode", MODES[args.mode.lower()]),
        ("colour", "hex{}".format(args.color)),
        ("pp", "1"),
        ("countryrank", ""),
        ("xpbar", ""),
    )))
    return Response("osu! signature for **{}** (via <http://lemmmy.pw/osusig/>)".format(args.username),
                    attachments=[await fetch_image(url)])
