"""Search for images using Bing.com."""

import random

from aiohttp import BasicAuth
from plumeria import config, scoped_config
from plumeria.command import commands, CommandError
from plumeria.command.parse import Text
from plumeria.config.common import nsfw
from plumeria.message import Response
from plumeria.plugin import PluginSetupError
from plumeria.util import http
from plumeria.util.collections import SafeStructure
from plumeria.util.ratelimit import rate_limit

SEARCH_URL = "https://api.datamarket.azure.com/Bing/Search/v1/Image"

api_key = config.create("bing", "key",
                        fallback="",
                        comment="An API key from Bing")


@commands.create("image", "images", "i", category="Search", params=[Text('query')])
@rate_limit()
async def image(message, query):
    """
    Search Bing for an image and returns a URL to that image.

    Example::

        image socially awkward penguin

    """
    r = await http.get(SEARCH_URL, params=[
        ('$format', 'json'),
        ('$top', '20'),
        ('Adult', "'Off'" if scoped_config.get(nsfw, message.channel) else "'Strict'"),
        ('Query', "'{}'".format(query)),
    ], auth=BasicAuth("", password=api_key()))
    results = SafeStructure(r.json()).d.results
    if results:
        return Response(random.choice(results).MediaUrl)
    else:
        raise CommandError("no results found")


def setup():
    config.add(api_key)

    if not api_key():
        raise PluginSetupError("This plugin requires a Bing.com API key. Registration is free as of writing but "
                               "Microsoft plans to charge for service.")

    commands.add(image)
