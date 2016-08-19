import collections
from ..util.http import BaseRestClient

Deal = collections.namedtuple("Deal", "id name price url")


class CheapShark(BaseRestClient):
    async def search(self, query):
        json = await self.request("get", "http://www.cheapshark.com/api/1.0/games", params=dict(title=query, limit=1))
        if len(json):
            url = "http://www.cheapshark.com/redirect?dealID={}".format(json[0]['cheapestDealID'])
            return Deal(json[0]['cheapestDealID'], json[0]['external'], json[0]['cheapest'], url)