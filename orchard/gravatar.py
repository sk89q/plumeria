"""Get a person's Gravatar avatar."""

import hashlib

from plumeria.command import commands, CommandError
from plumeria.util.ratelimit import rate_limit


@commands.create("gravatar", "grav", category="Search")
@rate_limit()
async def gravatar(message):
    """
    Gets the Gravatar for an email address.

    Example::

        /gravatar example@example.com

    """
    q = message.content.strip()
    if not q:
        raise CommandError("Search term required!")
    return "https://www.gravatar.com/avatar/{}".format(hashlib.md5(q.encode('utf-8')).hexdigest())


def setup():
    commands.add(gravatar)
