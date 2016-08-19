import collections
import asyncio
from valve.source.a2s import ServerQuerier

ServerResponse = collections.namedtuple("ServerResponse", "info players")
Player = collections.namedtuple("Player", "name duration score")


async def steam_query(address, timeout=2.):
    def query():
        players = []
        server = ServerQuerier(address, timeout=timeout)
        server_info = dict(server.get_info().items())
        for player in server.get_players().get("players"):
            if len(player.get("name")):
                players.append(Player(player.get("name"), player.get("duration"), player.get("score")))
        return ServerResponse(server_info, players)

    return await asyncio.get_event_loop().run_in_executor(None, query)
