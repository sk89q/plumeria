"""Search YouTube for videos."""
import collections

from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.message import Response
from plumeria.plugin import PluginSetupError
from plumeria.util.http import BaseRestClient
from plumeria.util.ratelimit import rate_limit

api_key = config.create("youtube", "key",
                        fallback="",
                        comment="A YouTube API key. API keys can be registered at "
                                "https://console.developers.google.com/")

YouTubeVideo = collections.namedtuple("YouTubeVideo", "id title description url")


class YouTube(BaseRestClient):
    _api_key = None

    @property
    def api_key(self):
        return self._api_key or api_key()

    @api_key.setter
    def api_key(self, value):
        self._api_key = value

    async def search(self, query):
        json = await self.request("get", "https://www.googleapis.com/youtube/v3/search", params={
            "key": self.api_key,
            "part": "snippet",
            "maxResults": 5,
            "order": "relevance",
            "q": query,
            "safeSearch": "none",
            "type": "video"
        })
        videos = []
        for item in json['items']:
            videos.append(YouTubeVideo(item['id']['videoId'],
                                       item['snippet']['title'],
                                       item['snippet']['description'],
                                       "https://www.youtube.com/watch?v={}".format(item['id']['videoId'])))
        return videos


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
    config.add(api_key)

    if not api_key():
        raise PluginSetupError("This plugin requires an API key from Google. Registration is free. Get keys from "
                               "https://console.developers.google.com.")

    commands.add(yt)
