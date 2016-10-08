from plumeria.middleware.api.youtube import YouTube
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
