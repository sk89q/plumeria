"""Search YouTube for videos."""

from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.message import Response
from plumeria.middleware.api.youtube import YouTube, default_api_key
from plumeria.plugin import PluginSetupError
from plumeria.util.ratelimit import rate_limit

youtube = YouTube()


@commands.create('youtube', 'yt', 'ytsearch', cost=2, category='Search')
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


def setup():
    config.add(default_api_key)

    if not default_api_key():
        raise PluginSetupError("This plugin requires an API key from Google. Registration is free. Get keys from "
                               "https://console.developers.google.com.")

    commands.add(yt)
