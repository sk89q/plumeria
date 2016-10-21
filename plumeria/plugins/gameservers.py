"""Query Valve game server status and player lists."""

import valve
from plumeria.command import commands, CommandError
from plumeria.games import steam_query
from plumeria.message import Response
from plumeria.util.ratelimit import rate_limit
from plumeria.util.network import AddressResolver, InvalidAddress

resolver = AddressResolver(port_validator=lambda p: p >= 1000)


@commands.create('a2squery', category='Servers')
@rate_limit()
async def a2squery(message):
    """
    Query a game server using Valve's A2S query protocol.

    Works for Source games but also for other games.

    Example::

        /a2squery example.com:27015
    """
    try:
        address = await resolver.resolve(message.content, 27015)
        resp = await steam_query(address)
        if len(resp.players):
            text = "{} online: {}".format(len(resp.players), ", ".join([p.name for p in resp.players]))
        else:
            text = "No players online"
        return Response(text)
    except InvalidAddress as e:
        raise CommandError(str(e))
    except valve.source.a2s.NoResponseError as e:
        raise CommandError("Failed to query server info: {}".format(str(e)))


def setup():
    commands.add(a2squery)
