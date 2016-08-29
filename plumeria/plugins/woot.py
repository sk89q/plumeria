import re
from functools import reduce

from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.util import http
from plumeria.util.message import strip_html
from plumeria.util.ratelimit import rate_limit

api_key = config.create("woot", "key",
                        fallback="",
                        comment="An API key from woot.com")


@commands.register("woot", category="Search")
@rate_limit()
async def woot(message):
    """
    Get the daily deals on woot.com.

    Example::

        /woot

    """
    r = await http.get("http://api.woot.com/2/events.json", params=[
        ('key', api_key()),
        ('eventType', 'Daily'),
    ])
    data = r.json()
    offers = map(lambda e: e['Offers'], data)
    offers = reduce(lambda x, y: x + y, offers)
    return "\n".join(map(lambda e: "\u2022 **{title}:** (${price:.2f}) [{remaining}%] <{url}>".format(
        title=e['Title'],
        teaser=strip_html(e['Teaser']),
        price=sum(map(lambda x: x['SalePrice'], e['Items'])),
        url=re.sub("\\?.*$", "", e['Url']),
        remaining=e['PercentageRemaining'],
    ), offers))
