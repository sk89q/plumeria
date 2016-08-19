from plumeria.command import commands, CommandError
from plumeria.message import Response
from plumeria.util.ratelimit import rate_limit
from plumeria.api.lastfm import LastFm

lastfm = LastFm()


@commands.register('lastscrobble', category='last.fm')
@rate_limit()
async def lastscrobble(message):
    """
    Gets the last scrobbled song of a user.
    """
    if len(message.content):
        tracks = await lastfm.recent_tracks(message.content)
        if len(tracks):
            return Response("{} - {}".format(tracks[0].artist, tracks[0].title))
        else:
            raise CommandError("No tracks have been scrobbled by that user.")


@commands.register('tagtop', category='last.fm')
@rate_limit()
async def tagtop(message):
    """
    Gets the top track for a music tag using last.fm.
    """
    if len(message.content):
        tracks = await lastfm.tag_tracks(message.content)
        if len(tracks):
            return Response("{} - {}".format(tracks[0].artist, tracks[0].title))
        else:
            raise CommandError("Last.fm doesn't know about that tag.")
