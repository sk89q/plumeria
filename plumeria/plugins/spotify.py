import re

from plumeria.command import commands, CommandError
from plumeria.util import http
from plumeria.util.ratelimit import rate_limit

RESULT_LIMIT = 8


@commands.register("spotify artist", "spotify", "spartist", category="Search")
@rate_limit()
async def artist(message):
    """
    Search Spotify for artists.

    """
    q = message.content.strip()
    if not len(q):
        raise CommandError("Search term required!")
    r = await http.get("https://api.spotify.com/v1/search", params=[
        ('q', q),
        ('type', 'artist')
    ])
    data = r.json()
    if len(data['artists']['items']):
        results = map(lambda item: "\u2022 **{}**: {} <{}>".format(
            item['name'],
            item['genres'][0] if len(item['genres']) else "unknown genre",
            item['external_urls']['spotify']), data['artists']['items'][:RESULT_LIMIT])
        return "Spotify artist search:\n{}".format("\n".join(results))
    else:
        raise CommandError("no results found")


@commands.register("spotify track", "sptrack", category="Search")
@rate_limit()
async def track(message):
    """
    Search Spotify for tracks.

    """
    q = message.content.strip()
    if not len(q):
        raise CommandError("Search term required!")
    r = await http.get("https://api.spotify.com/v1/search", params=[
        ('q', q),
        ('type', 'track')
    ])
    data = r.json()
    if len(data['tracks']['items']):
        results = map(lambda item: "\u2022 **{}** by *{}* <{}>".format(
            item['name'],
            item['artists'][0]['name'],
            item['external_urls']['spotify']), data['tracks']['items'][:RESULT_LIMIT])
        return "Spotify track search:\n{}".format("\n".join(results))
    else:
        raise CommandError("no results found")


@commands.register("spotify album", "spalbum", category="Search")
@rate_limit()
async def album(message):
    """
    Search Spotify for albums.

    """
    q = message.content.strip()
    if not len(q):
        raise CommandError("Search term required!")
    r = await http.get("https://api.spotify.com/v1/search", params=[
        ('q', q),
        ('type', 'album')
    ])
    data = r.json()
    if len(data['albums']['items']):
        results = map(lambda item: "\u2022 **{}** <{}>".format(
            item['name'],
            item['external_urls']['spotify']), data['albums']['items'][:RESULT_LIMIT])
        return "Spotify album search:\n{}".format("\n".join(results))
    else:
        raise CommandError("no results found")
