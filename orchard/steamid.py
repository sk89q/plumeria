"""Commands to look up and convert Steam community ID and profiles."""

from plumeria.command import commands, CommandError
from plumeria.middleware.api.steam import SteamCommunity, parse_steam_id
from plumeria.util.ratelimit import rate_limit

steam_community = SteamCommunity()


@commands.create("steam id", "steamid", category="Steam")
@rate_limit()
async def steamid(message):
    """
    Look up variants of a Steam's user ID.
    """
    s = message.content.strip()
    id = await parse_steam_id(s)
    return "**ID64:** {}\n**ID32:** {}\n**URL:** {}".format(
        id.to_64(),
        id.to_text(),
        id.community_url(),
    )


@commands.create("steam profile", "steamprofile", category="Steam")
@rate_limit()
async def steamprofile(message):
    """
    Get information from a Steam profile.
    """
    s = message.content.strip()
    id = await parse_steam_id(s)
    profile = await steam_community.steam_profile(id.to_64(), id64=True)
    return "**{}**\n{} / {}\nhttps://steamcommunity/profiles/{}".format(
        profile.name or "(no name)",
        profile.id.to_64(),
        profile.id.to_text(),
        profile.id.to_64())


@commands.create("steam avatar", "steamavatar", category="Steam")
@rate_limit()
async def steam_avatar(message):
    """
    Get a Steam profile avatar URL.
    """
    s = message.content.strip()
    id = await parse_steam_id(s)
    profile = await steam_community.steam_profile(id.to_64(), id64=True)
    if profile.avatar:
        return profile.avatar
    else:
        raise CommandError("The user has no avatar.")


@commands.create("steam id64", "steamid64", category="Steam")
@rate_limit()
async def steamid_64(message):
    """
    Get a Steam user's 64-bit ID.
    """
    s = message.content.strip()
    return str((await parse_steam_id(s)).to_64())


@commands.create("steam id32", "steamid32", category="Steam")
@rate_limit()
async def steamid_32(message):
    """
    Get a Steam user's 32-bit ID.
    """
    s = message.content.strip()
    return (await parse_steam_id(s)).to_text()


def setup():
    commands.add(steamid)
    commands.add(steamprofile)
    commands.add(steam_avatar)
    commands.add(steamid_64)
    commands.add(steamid_32)
