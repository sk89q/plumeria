from plumeria.command import commands, CommandError
from plumeria.message import Response
from plumeria.util.ratelimit import rate_limit
from plumeria.api.cheapshark import CheapShark

cheapshark = CheapShark()


@commands.register('cheapshark', 'gameprice', category='Search')
@rate_limit()
async def price(message):
    """
    Searches CheapShark.com for game deals for a search query.

    CheapShark gets pricing data from select game stores and does not have special deals at other websites. Prices
    are returned in US Dollar.
    """
    if len(message.content.strip()):
        deal = await cheapshark.search(message.content)
        if deal:
            return Response("{} at ${} USD - {}".format(deal.name, deal.price, deal.url))
        else:
            raise CommandError("Couldn't find that game on CheapShark")
