import re

from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.util import http
from plumeria.util.message.geo import match_country
from plumeria.util.ratelimit import rate_limit

LYRICS_CLEAN_PATTERN = re.compile("\\*+ This Lyrics is NOT for Commercial use \\*+", re.I)
COPYRIGHT_CLEAN_PATTERN = re.compile("This Lyrics is NOT for Commercial use and only 30% of the lyrics are returned.",
                                     re.I)

api_key = config.create("musicmatch", "key",
                        fallback="",
                        comment="An API key from https://developer.musixmatch.com/")


def clean_lyrics(s):
    return LYRICS_CLEAN_PATTERN.sub("", s).strip()


def clean_copyright(s):
    return COPYRIGHT_CLEAN_PATTERN.sub("FOR NON-COMMERCIAL USE.", s).strip()


@commands.register("artist charts", "acharts", category="Music")
@rate_limit()
async def charts(message):
    """
    Get the top charting artists in a country, defaulting to USA if no country is
    provided. Powered by Musicmatch.

    Example::

        /acharts it

    Response::

        \u2022 Il Pagante (Electronic)
        \u2022 Alvaro Soler (Pop in Spanish)
        \u2022 twenty one pilots (Alternative)
        \u2022 Coldplay (Alternative)
        \u2022 Alessandra Amoroso (Pop)

    """
    q = message.content.strip()
    if not q:
        q = "us"
    country = match_country(q)

    r = await http.get("http://api.musixmatch.com/ws/1.1/chart.artists.get", params=[
        ('apikey', api_key()),
        ('page', '1'),
        ('page_size', '10'),
        ('country', country.alpha2),
    ])
    data = r.json()

    def map_artist(e):
        genre = e['artist']['primary_genres']['music_genre_list'][0]['music_genre']['music_genre_name'] if len(
            e['artist']['primary_genres']['music_genre_list']) else "?"
        return "\u2022 {name} ({genre})".format(
            name=e['artist']['artist_name'],
            genre=genre,
        )

    return '\n'.join(map(map_artist, data['message']['body']['artist_list']))


@commands.register("charts", category="Music")
@rate_limit()
async def charts(message):
    """
    Get the top charting songs in a country, defaulting to USA if no country is
    provided. Powered by Musicmatch.

    Example::

        /charts us

    Response::

        \u2022 The Chainsmokers feat. Halsey - Closer (Dance)
        \u2022 twenty one pilots - Heathens (?)
        \u2022 Britney Spears feat. G-Eazy - Make Me... (Pop)
        \u2022 Charlie Puth feat. Selena Gomez - We Don’t Talk Anymore (?)
        \u2022 Shawn Mendes - Treat You Better (Pop)

    """
    q = message.content.strip()
    if not q:
        q = "us"
    country = match_country(q)

    r = await http.get("http://api.musixmatch.com/ws/1.1/chart.tracks.get", params=[
        ('apikey', api_key()),
        ('page', '1'),
        ('page_size', '10'),
        ('country', country.alpha2),
    ])
    data = r.json()

    def map_track(e):
        genre = e['track']['primary_genres']['music_genre_list'][0]['music_genre']['music_genre_name'] if len(
            e['track']['primary_genres']['music_genre_list']) else "?"
        return "\u2022 {artist} - {name} ({genre})".format(
            artist=e['track']['artist_name'],
            name=e['track']['track_name'],
            genre=genre,
        )

    return '\n'.join(map(map_track, data['message']['body']['track_list']))


@commands.register("lyrics", category="Music")
@rate_limit()
async def lyrics(message):
    """
    Get some of the lyrics of a song, given artist and title. Powered by
    Musicmatch.

    Example::

        /lyrics satellite stories - a great escape

    """
    q = message.content.strip()
    if not q:
        raise CommandError("Search term required!")
    r = await http.get("http://api.musixmatch.com/ws/1.1/track.search", params=[
        ('apikey', api_key()),
        ('f_has_lyrics', '1'),
        ('q', q),
    ])
    data = r.json()
    if len(data['message']['body']['track_list']):
        track = data['message']['body']['track_list'][0]['track']
        track_id = track['track_id']
        artist = track['artist_name']
        name = track['track_name']
        r = await http.get("http://api.musixmatch.com/ws/1.1/track.lyrics.get", params=[
            ('apikey', api_key()),
            ('track_id', str(track_id)),
        ])
        data = r.json()
        copyright = clean_copyright(data['message']['body']['lyrics']['lyrics_copyright'])
        lyrics = clean_lyrics(data['message']['body']['lyrics']['lyrics_body'])
        return "**{artist} - {name}**\n{lyrics}\n`{copyright}`".format(
            artist=artist,
            name=name,
            lyrics=lyrics,
            copyright=copyright)
    else:
        return "no results (maybe lyrics are not available)"
