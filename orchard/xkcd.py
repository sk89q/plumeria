"""Get xkcd comics by ID or get the latest."""

from plumeria.command import commands, CommandError
from plumeria.util import http
from plumeria.util.http import BadStatusCodeError
from plumeria.util.ratelimit import rate_limit


@commands.create("xkcd", category="Search")
@rate_limit()
async def xkcd(message):
    """
    Get a certain XKCD comic or the latest one. Provide a number to get
    a certain comic number.

    Example::

        /xkcd
        /xkcd 123

    """
    q = message.content.strip()
    if not q:
        r = await http.get("https://xkcd.com/info.0.json")
        data = r.json()
        return data['img']
    else:
        try:
            id = int(q)
            r = await http.get("https://xkcd.com/{}/info.0.json".format(id))
            data = r.json()
            return data['img']
        except BadStatusCodeError:
            raise CommandError("comic does not exist or other error")
        except ValueError:
            raise CommandError("number expected")


def setup():
    commands.add(xkcd)
