from collections import namedtuple

from plumeria.command import commands
from plumeria.message import Response
from plumeria.util.http import APIError, DefaultClientSession
from plumeria.util.ratelimit import rate_limit

STEAM_STATUS_URL = "https://crowbar.steamdb.info/Barney"

SteamStatus = namedtuple("SteamStatus", "online store community web_api steamos_repo")

async def get_steam_status():
    with DefaultClientSession() as session:
        async with session.get(STEAM_STATUS_URL) as resp:
            if resp.status != 200:
                raise APIError("HTTP code is not 200; got {}".format(resp.status))
            data = await resp.json()
            return SteamStatus(data['services']['online']['title'],
                               data['services']['store']['title'],
                               data['services']['community']['title'],
                               data['services']['webapi']['title'],
                               data['services']['repo']['title'],
                               )


@commands.register("steamstatus", category="Steam")
@rate_limit()
async def steam_status(message):
    """
    Get the status of Steam's services, including the number of users online.

    Uses steamstat.us for status information.

    """
    status = await get_steam_status()
    return Response("{} online\nStore: {}\nCommunity: {}\nWeb API: {}\nSteam OS Repo: {}".format(
        status.online,
        status.store,
        status.community,
        status.web_api,
        status.steamos_repo
    ))
