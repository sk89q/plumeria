from random import randint

from plumeria.api.youtube import YouTube
from plumeria.command import commands, CommandError, channel_only
from plumeria.message import Response
from plumeria.util.ratelimit import rate_limit

youtube = YouTube()


@commands.register('youtube', 'yt', 'ytsearch', cost=2, category='Search')
@rate_limit()
async def yt(message):
    """
    Search YouTube for a video.

    Example::

        /yt knuckle puck copacetic
    """
    if len(message.content.strip()):
        videos = await youtube.search(message.content)
        if len(videos):
            return Response(videos[0].url)
        else:
            raise CommandError("No video found!")


@commands.register('mcmusic', 'overusedmusic', cost=2, category='Fun')
@rate_limit()
async def mcmusic():
    """
    List topviewed NCS videos and select 1 at random.

    Example::

        /mcmusic
    """
    videos = await youtube.searchExtended("UC_aEa8K-EOJ3D6gOs7HcyNg", "viewcount", 50)
    if len(videos):
        return Response(videos[randint(0, len(videos))].url)
    else:
        raise CommandError("No video found!")
