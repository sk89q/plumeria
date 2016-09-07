import collections
from .. import config
from ..util.http import BaseRestClient

default_api_key = config.create("youtube", "key",
                                fallback="unset",
                                comment="A YouTube API key. API keys can be registered at "
                                "https://console.developers.google.com/")

YouTubeVideo = collections.namedtuple("YouTubeVideo", "id title description url")


class YouTube(BaseRestClient):
    _api_key = None

    @property
    def api_key(self):
        return self._api_key or default_api_key()

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
    async def searchExtended(self, channelId, sortby, maxresults):
        json = await self.request("get", "https://www.googleapis.com/youtube/v3/search", params={
            "key": self.api_key,
            "part": "snippet",
            "maxResults": maxresults,
            "order": sortby,
            "channelId": channelId
        })
        videos = []
        for item in json['items']:
            videos.append(YouTubeVideo(item['id']['videoId'],
                                       item['snippet']['title'],
                                       item['snippet']['description'],
                                       "https://www.youtube.com/watch?v={}".format(item['id']['videoId'])))
        return videos
