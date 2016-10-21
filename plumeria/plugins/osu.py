"""Commands to query osu! (a game) stats for a user."""

import shlex
import urllib.parse
import re

from plumeria import config
from plumeria.command import commands, CommandError, ArgumentParser
from plumeria.message import Response
from plumeria.plugin import PluginSetupError
from plumeria.util import http
from plumeria.message.image import fetch_image
from plumeria.util.ratelimit import rate_limit

HEX_COLOR_PATTERN = re.compile("^#?([a-f0-9]{6})$")
USERNAME_PATTERN = re.compile("^[^/ ]+$")  # overly permissive
MODES = {'default': 0, 'taiko': 1, 'ctb': 2, 'mania': 3}

api_key = config.create("osu", "key",
                        fallback="",
                        comment="An API key from https://osu.ppy.sh")


def validate_username(s):
    if USERNAME_PATTERN.match(s):
        return s
    raise CommandError("Invalid osu! username")


def validate_hex_color(s):
    m = HEX_COLOR_PATTERN.search(s)
    if m:
        return m.group(1)
    raise CommandError("Invalid hex color code")


@commands.create("osu sig", "osusig", category="Games")
@rate_limit()
async def sig(message):
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


@commands.create("osu stats", "osu", category="Games")
@rate_limit()
async def stats(message):
    """
    Get the stats for an osu! user. Arguments are:

    * Username
    * (optional) Mode (of default, taiko, ctb, or mania)

    Example::

        /osu example

    Response::

        Example (US)
        Level: 41.434 / Play Count: 4370
        PP: 626.781 / PP Rank: 59309
        Accuracy: 92.149%
        300s: 280515 / 100s: 62478 / 50s: 13248 / SS: 14 / S: 151 / A: 59

    """
    parser = ArgumentParser()
    parser.add_argument("username", type=validate_username)
    parser.add_argument("mode", nargs='?', default="default", choices=MODES.keys())
    args = parser.parse_args(shlex.split(message.content))
    r = await http.get("https://osu.ppy.sh/api/get_user", params=[
        ('k', api_key()),
        ('u', args.username),
        ('m', MODES[args.mode.lower()]),
    ])
    data = r.json()
    if len(data):
        for key in ('level', 'playcount', 'pp_raw', 'pp_rank', 'accuracy', 'count300', 'count100', 'count50',
                    'count_rank_ss', 'count_rank_s', 'count_rank_a'):
            data[0][key] = float(data[0][key])
        return "**{username}** ({country})\n" \
               "Level: {level:.3f} / Play Count: {playcount:.0f}\n" \
               "PP: {pp_raw:.3f} / PP Rank: {pp_rank:.0f}\n" \
               "Accuracy: {accuracy:.3f}%\n" \
               "300s: {count300:.0f} / 100s: {count100:.0f} / 50s: {count50:.0f} / " \
               "SS: {count_rank_ss:.0f} / S: {count_rank_s:.0f} / A: {count_rank_a:.0f}".format(**data[0])
    else:
        return "no results"


def setup():
    config.add(api_key)

    if not api_key():
        raise PluginSetupError("This plugin requires an API key from https://osu.ppy.sh/. Registration is free, but "
                               "you have to download and install the game to complete registration.")

    commands.add(sig)
    commands.add(stats)
