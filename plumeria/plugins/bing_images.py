from aiohttp import BasicAuth
from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.message import Response
from plumeria.util import http
from plumeria.util.ratelimit import rate_limit

SEARCH_URL = "https://api.datamarket.azure.com/Bing/Search/v1/Image"

api_key = config.create("bing", "key",
                        fallback="unset",
                        comment="An API key from Bing")


@commands.register("image", "images", "i", category="Search")
@rate_limit()
async def image(message):
    """
    Search Bing for an image.

    """
    q = message.content.strip()
    if not q:
        raise CommandError("Search term required!")
    r = await http.get(SEARCH_URL, params=[
        ('$format', 'json'),
        ('$top', '10'),
        ('Query', "'{}'".format(q)),
    ], auth=BasicAuth("", password=api_key()))
    data = r.json()['d']
    if len(data['results']):
        return Response(data['results'][0]['MediaUrl'])
    else:
        raise CommandError("no results found")
