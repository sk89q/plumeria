import collections
from plumeria import config
from plumeria.util.http import BaseRestClient, APIError

default_api_key = config.create("lastfm", "key",
                                fallback="unset",
                                comment="An API key from last.fm")

Track = collections.namedtuple("Track", "artist title url")


class LastFm(BaseRestClient):
    URL = "http://ws.audioscrobbler.com/2.0/"
    _api_key = None

    @property
    def api_key(self):
        return self._api_key or default_api_key()

    @api_key.setter
    def api_key(self, value):
        self._api_key = value

    def preprocess(self, json):
        if 'error' in json:
            raise APIError(json['message'])
        return json

    async def recent_tracks(self, username):
        json = await self.request("get", self.URL, params={
            'method': "user.getrecenttracks",
            'user': username,
            'format': 'json',
            'api_key': self.api_key,
        })
        return [Track(i['artist']['#text'], i['name'], i['url']) for i in json['recenttracks']['track']]

    async def tag_tracks(self, tag):
        json = await self.request("get", self.URL, params={
            'method': "tag.gettoptracks",
            'tag': tag,
            'format': 'json',
            'api_key': self.api_key,
        })
        return [Track(i['artist']['name'], i['name'], i['url']) for i in json['tracks']['track']]
