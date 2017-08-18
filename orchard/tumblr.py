"""Search Tumblr."""

import random

from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.command.parse import Text, Word
from plumeria.plugin import PluginSetupError
from plumeria.util import http
from plumeria.util.http import BadStatusCodeError
from plumeria.util.ratelimit import rate_limit

api_key = config.create("tumblr", "consumer_key",
                        fallback="",
                        comment="A Tumblr OAuth API key. API keys can be registered at "
                                "https://www.tumblr.com/oauth/apps")


def collect_photos(posts):
    options = []
    for entry in posts:
        if 'photos' in entry:
            for photo in entry['photos']:
                options.append(photo['original_size']['url'])
    return options


@commands.create('tumblr tag', 'tumblrtag', 'ttag', cost=2, category='Search', params=[Text('query')])
@rate_limit()
async def search_tag(message, query):
    """
    Search Tumblr for a random image having a tag.

    Example::

        /tumblr tag royal blood

    """
    r = await http.get("https://api.tumblr.com/v2/tagged", params={
        "tag": query,
        "api_key": api_key()
    })
    data = r.json()

    options = collect_photos(data['response'])

    if not len(options):
        raise CommandError("No images found with the tag '{tag}'.".format(tag=query))

    return random.choice(options)


@commands.create('tumblr blog', 'tumblr', cost=2, category='Search', params=[Word('query')])
@rate_limit()
async def search_blog(message, query):
    """
    Get a random image from a user's Tumblr.

    Example::

        /tumblr waterparksband

    """
    try:
        r = await http.get("https://api.tumblr.com/v2/blog/{query}/posts/photo".format(query=query), params={
            "api_key": api_key()
        })
        data = r.json()
    except BadStatusCodeError as e:
        if e.http_code == 404:
            raise CommandError("No blog at {query}.tumblr.com.".format(query=query))
        raise

    options = collect_photos(data['response']['posts'])

    if not len(options):
        raise CommandError("No images found on {query}.tumblr.com'.".format(query=query))

    return random.choice(options)


def setup():
    config.add(api_key)

    if not api_key():
        raise PluginSetupError("This plugin requires an API key from Tumblr. Registration is free. Get keys from "
                               "https://www.tumblr.com/oauth/apps.")

    commands.add(search_tag)
    commands.add(search_blog)
