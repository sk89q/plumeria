"""Search CheapShark.com for deals."""

import collections

from plumeria.command import commands, CommandError
from plumeria.message import Response
from plumeria.util.ratelimit import rate_limit
from ..util.http import BaseRestClient

Deal = collections.namedtuple("Deal", "id name price url")


class CheapShark(BaseRestClient):
    async def search(self, query):
        json = await self.request("get", "http://www.cheapshark.com/api/1.0/games", params=dict(title=query, limit=1))
        if len(json):
            url = "http://www.cheapshark.com/redirect?dealID={}".format(json[0]['cheapestDealID'])
            return Deal(json[0]['cheapestDealID'], json[0]['external'], json[0]['cheapest'], url)


cheapshark = CheapShark()


@commands.create('cheapshark', 'gameprice', category='Search')
@rate_limit()
async def price(message):
    """
    Searches CheapShark.com for game deals for a search query.

    CheapShark gets pricing data from select game stores and does not have special deals at other websites. Prices
    are returned in US Dollars.

    Example::

        /cheapshark overwatch

    Response::

        Overwatch Origins Edition at $45.99 USD - http://www.cheapshark.com/[...]
    """
    if len(message.content.strip()):
        deal = await cheapshark.search(message.content)
        if deal:
            return Response("{} at ${} USD - {}".format(deal.name, deal.price, deal.url))
        else:
            raise CommandError("Couldn't find that game on CheapShark")


def setup():
    commands.add(price)
