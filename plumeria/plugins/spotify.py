"""Search Spotify for music."""

from titlecase import titlecase

from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.message.lists import build_list
from plumeria.util import http
from plumeria.util.ratelimit import rate_limit

RESULT_LIMIT = 8

default_country = config.create("spotify", "default_country", fallback='US', comment="The default country for searches")

async def get_artist_id(q):
    r = await http.get("https://api.spotify.com/v1/search", params=[
        ('q', 'artist:' + q),
        ('type', 'artist')
    ])
    artist_data = r.json()
    if not len(artist_data['artists']['items']):
        raise CommandError("Couldn't find the supplied artist on Spotify.")
    return artist_data['artists']['items'][0]['id']


@commands.create("spotify artist", "spartist", category="Music")
@rate_limit()
async def artist(message):
    """
    Search Spotify for artists.

    Example::

        /spotify twenty one pilots

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


@commands.create("spotify track", "spotify", "sptrack", category="Music")
@rate_limit()
async def track(message):
    """
    Search Spotify for tracks.

    Example::

        /spotify '68 - track 1 r

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


@commands.create("spotify album", "spalbum", category="Music")
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


@commands.create("spotify discog", "discog", category="Music")
@rate_limit()
async def discog(message):
    """
    Get the albums of an artist.

    Example::

        /discog coheed and cambria

    """
    q = message.content.strip()
    if not len(q):
        raise CommandError("Search term required!")

    artist_id = await get_artist_id(q)

    r = await http.get("https://api.spotify.com/v1/artists/{}/albums".format(artist_id))
    data = r.json()
    if 'error' in data:
        raise CommandError(data['message'])

    seen_names = set() # there are 'duplicates' although they are not true duplicates
    items = []
    for e in data['items']:
        if e['name'] not in seen_names:
            items.append("**{name}** ({type}) - <{url}>".format(
                name=e['name'],
                type=titlecase(e['album_type']),
                url=e['external_urls']['spotify'],
            ))
            seen_names.add(e['name'])

    return build_list(items)


@commands.create("spotify top", "top songs", category="Music")
@rate_limit()
async def top_songs(message):
    """
    Get the top songs of an artist.

    Example::

        /top songs ah-ha

    """
    q = message.content.strip()
    if not len(q):
        raise CommandError("Search term required!")

    artist_id = await get_artist_id(q)

    r = await http.get("https://api.spotify.com/v1/artists/{}/top-tracks".format(artist_id), params=[
        ('country', default_country()),
    ])
    data = r.json()
    if 'error' in data:
        raise CommandError(data['message'])

    return build_list(["**{name}** ({album}) - <{url}>".format(
        name=e['name'],
        album=e['album']['name'],
        url=e['external_urls']['spotify'],
    ) for e in data['tracks']])


def setup():
    config.add(default_country)
    commands.add(artist)
    commands.add(track)
    commands.add(album)
    commands.add(discog)
    commands.add(top_songs)
