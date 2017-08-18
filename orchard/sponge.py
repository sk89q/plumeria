"""Looks up Sponge resources."""

import plumeria.util.http as http
from plumeria.command import commands, CommandError
from plumeria.command.parse import Text
from plumeria.message.lists import build_list
from plumeria.util.ratelimit import rate_limit


@commands.create("ore", category="Search", params=[Text('query')])
@rate_limit()
async def search(message, query):
    """
    Search for plugins on Ore.

    Example::

        ore protection

    """
    r = await http.get("https://ore.spongepowered.org/api/projects", params={
        "q": query,
    })
    results = r.json()

    if not results:
        raise CommandError("No results.")

    return build_list([
                          "**{name}** {description} - <https://ore.spongepowered.org{href}>".format(**item) for item in results[:10]
                          ])


def setup():
    commands.add(search)
