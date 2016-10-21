"""Query the Python package repository for packages."""

import asyncio
import xmlrpc.client as xmlrpclib

from plumeria.command import commands, CommandError
from plumeria.util.ratelimit import rate_limit

client = xmlrpclib.ServerProxy('https://pypi.python.org/pypi')


@commands.create("pypi", category="Development")
@rate_limit()
async def pypi(message):
    """
    Search the Python package repository for a package.

    Example::

        /pypi discord

    Response::

        \u2022 django-discord-bind (0.2.0) - A Django app for securely assoc[...]
        \u2022 discord.py (0.11.0) - A python wrapper for the Discord API ht[...]
        \u2022 PyDiscord (1.0.1) - A simple module for converting dates from[...]
    """
    q = message.content.strip()
    if not q:
        raise CommandError("Search term required!")

    def execute():
        return client.search({'name': q})

    data = await asyncio.get_event_loop().run_in_executor(None, execute)
    if len(data):
        return "\n".join(map(lambda e:
                             "\u2022 **{name}** ({version}) - {desc} <https://pypi.python.org/pypi/{name}>".format(
                                 name=e['name'],
                                 version=e['version'],
                                 desc=e['summary']),
                             data))
    else:
        raise CommandError("no results found")


def setup():
    commands.add(pypi)
