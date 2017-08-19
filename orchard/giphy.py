"""Search Giphy."""

import random

from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.command.parse import Text
from plumeria.plugin import PluginSetupError
from plumeria.util import http
from plumeria.util.ratelimit import rate_limit

api_key = config.create("giphy", "key",
                        fallback="",
                        comment="A Giphy API key. API keys can be registered at "
                                "https://developers.giphy.com/dashboard/")


def collect_photos(posts):
    options = []
    for entry in posts:
        if 'photos' in entry:
            for photo in entry['photos']:
                options.append(photo['original_size']['url'])
    return options


@commands.create('giphy', cost=2, category='Search', params=[Text('query')])
@rate_limit()
async def search(message, query):
    """
    Search Giphy for images and pick a random one.

    Example::

        /giphy all time low

    """
    r = await http.get("https://api.giphy.com/v1/gifs/search", params={
        "q": query,
        "api_key": api_key()
    })
    data = r.json()

    if not len(data['data']):
        raise CommandError("No results matching '{}'.".format(query))

    return random.choice(data['data'])['url']


@commands.create('sticker', cost=2, category='Search', params=[Text('query')])
@rate_limit()
async def sticker(message, query):
    """
    Search Giphy for stickers and pick a random one.

    Example::

        /sticker happy

    """
    r = await http.get("https://api.giphy.com/v1/stickers/search", params={
        "q": query,
        "api_key": api_key()
    })
    data = r.json()

    if not len(data['data']):
        raise CommandError("No results matching '{}'.".format(query))

    return random.choice(data['data'])['url']


def setup():
    config.add(api_key)

    if not api_key():
        raise PluginSetupError("This plugin requires an API key from Giphy. Registration is free. Get keys from "
                               "https://developers.giphy.com/dashboard/.")

    commands.add(search)
    commands.add(sticker)
