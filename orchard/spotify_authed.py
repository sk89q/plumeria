"""Let users access their own personal Spotify account."""

import random

from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.message.lists import build_list
from plumeria.core.oauth import oauth_manager, catch_token_expiration
from plumeria.perms import direct_only
from plumeria.plugin import PluginSetupError
from plumeria.transport import User
from plumeria.util import http
from plumeria.util.ratelimit import rate_limit
from plumeria.util.string import get_best_matching

client_id = config.create("spotify", "client_id",
                          fallback="",
                          comment="A Spotify OAuth client ID")

client_secret = config.create("spotify", "client_secret",
                              fallback="",
                              comment="A Spotify OAuth client secret")

spotify_endpoint = oauth_manager.create_oauth2(
    name="spotify",
    client_id=client_id,
    client_secret=client_secret,
    auth_url="https://accounts.spotify.com/authorize",
    token_url="https://accounts.spotify.com/api/token",
    requested_scopes=('playlist-read-private', 'playlist-read-collaborative',
                      'playlist-modify-public', 'playlist-modify-private',
                      'user-follow-modify', 'user-follow-read',
                      'user-library-read', 'user-library-modify',
                      'user-top-read'))


@catch_token_expiration(spotify_endpoint)
async def fetch_api(user: User, *args, **kwargs):
    if 'headers' not in kwargs:
        kwargs['headers'] = []
    kwargs['headers'].append(('Authorization', await spotify_endpoint.get_auth_header(user)))
    r = await http.get(*args, **kwargs)
    data = r.json()
    if 'error' in data:
        raise CommandError(data['message'])
    return data


async def fetch_paged_list(*args, limit=20, max_page_count=1, **kwargs):
    base_params = dict(kwargs['params'] if 'params' in kwargs else [])
    base_params['limit'] = limit
    items = []
    offset = 0
    for i in range(max_page_count):
        kwargs['params'] = dict(base_params)
        kwargs['params']['offset'] = offset
        data = await fetch_api(*args, **kwargs)
        items += data['items']
        if data['next'] is None:
            break
        else:
            offset = data['offset'] + data['limit']
    return items


@commands.create("spotify playlists", category="Music")
@direct_only
@rate_limit()
async def playlists(message):
    """
    Get a list of your public Spotify playlists.

    Example::

        /spotify playlists

    """

    data = await fetch_api(message.author, "https://api.spotify.com/v1/me/playlists", params=[
        ('limit', '50'),
    ])

    public_playlists = [e for e in data['items'] if e['public']]

    if not len(public_playlists):
        raise CommandError("You have no public playlists.")

    return build_list(["**{name}** - <{url}>".format(
        name=e['name'],
        url=e['external_urls']['spotify'],
    ) for e in public_playlists])


@commands.create("spotify pick", category="Music")
@direct_only
@rate_limit()
async def pick_song(message):
    """
    Pick 5 random songs from one of your playlists searched by name.

    Example::

        /spotify pick classic rock 2010

    The command will only check your first 100 playlists to see if they match
    your query, and then the command will only pick a random song from the first
    200 songs on the playlist.

    """
    query = message.content.strip()
    if not len(query):
        raise CommandError("Supply something to search for in playlist names.")

    playlists = await fetch_paged_list(message.author, "https://api.spotify.com/v1/me/playlists", limit=50,
                                       max_page_count=2)

    if not len(playlists):
        raise CommandError("You have no playlists.")

    best_playlists = get_best_matching(playlists, query, key=lambda item: item['name'])

    if not len(best_playlists):
        raise CommandError("No playlists (out of your first 100) matched your query.")

    owner_id = best_playlists[0]['owner']['id']

    tracks = await fetch_paged_list(message.author,
                                    "https://api.spotify.com/v1/users/{}/playlists/{}/tracks".format(
                                        owner_id, best_playlists[0]['id']
                                    ),
                                    limit=100, max_page_count=2)

    if not len(tracks):
        raise CommandError("The playlist '{}' has no tracks.".format(best_playlists[0]['name']))

    random.shuffle(tracks)

    return build_list(["**{artist} - {name}** - <{url}>".format(
        artist=e['track']['artists'][0]['name'],
        name=e['track']['name'],
        url=e['track']['external_urls']['spotify'] if 'spotify' in e['track']['external_urls'] else "local track",
    ) for e in tracks[:5]])


def setup():
    config.add(client_id)
    config.add(client_secret)

    if not client_id() or not client_secret():
        raise PluginSetupError("This plugin requires a client ID and client secret from Spotify. Registration is free. "
                               "Create an application on https://developer.spotify.com/my-applications/ to get "
                               "an ID and secret.")

    oauth_manager.add(spotify_endpoint)
    commands.add(playlists)
    commands.add(pick_song)
