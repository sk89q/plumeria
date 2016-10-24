import re
from collections import namedtuple

import aiohttp
from bs4 import BeautifulSoup
from valve.steam.id import SteamID as BrokenSteamID, UNIVERSE_INDIVIDUAL, TYPE_INDIVIDUAL, TYPE_CLAN, \
    community32_regex, community64_regex, letter_type_map, type_url_path_map, urlparse
from plumeria.command import CommandError
from plumeria.util.http import APIError, DefaultClientSession

COMMUNITY_URL_ID_PATTERN = re.compile("https?://(?:www\\.)?steamcommunity\\.com/profiles/([0-9]+)(?:/[^ ]*)?", re.I)
COMMUNITY_URL_NAME_PATTERN = re.compile("https?://(?:www\\.)?steamcommunity\\.com/id/([A-Za-z0-9_\\-]+)(?:/[^ ]*)?",
                                        re.I)
ID_TEXT_PATTERN = re.compile("(STEAM_[0-9]+:[0-9]+:[0-9]+)")
ID_64_PATTERN = re.compile("([0-9]{20,})")
ID_NAME_PATTERN = re.compile("^([A-Za-z0-9_\\-]+)$")

SteamProfile = namedtuple("SteamProfile", "id name state privacy avatar vac_banned")


class SteamID(BrokenSteamID):
    # broken python-valve in python 3.x
    @classmethod
    def from_community_url(cls, id, universe=UNIVERSE_INDIVIDUAL):
        url = urlparse.urlparse(id)
        match = community32_regex.match(url.path)
        if match:
            w = int(match.group("W"))
            y = w & 1
            z = (w - y) // 2  # fix: integer division
            return cls(z, y, letter_type_map[match.group("type")], universe)
        match = community64_regex.match(url.path)
        if match:
            w = int(match.group("W"))
            y = w & 1
            if match.group("path") in type_url_path_map[TYPE_INDIVIDUAL]:
                z = (w - y - 0x0110000100000000) // 2  # fix: integer division
                type = TYPE_INDIVIDUAL
            elif match.group("path") in type_url_path_map[TYPE_CLAN]:
                z = (w - y - 0x0170000000000000) // 2  # fix: integer division
                type = TYPE_CLAN

            return cls(z, y, type, universe)

    @classmethod
    def from_64(cls, s):
        return cls.from_community_url("https://steamcommunity.com/profiles/" + s)

    def to_64(self):
        if self.type == TYPE_INDIVIDUAL:
            return ((self.account_number + self.account_number) +
                    0x0110000100000000 + self.instance)
        elif self.type == TYPE_CLAN:
            return ((self.account_number + self.account_number) +
                    0x0170000000000000 + self.instance)

    def to_text(self):
        return "STEAM_{}:1:{}".format(self.type, (self.account_number * 2) + self.instance)


class SteamCommunity:
    async def steam_profile(self, s, id64=False):
        with DefaultClientSession() as session:
            if id64:
                url = "http://steamcommunity.com/profiles/" + str(s)
            else:
                url = "http://steamcommunity.com/id/" + s
            try:
                async with session.get(url, params={"xml": "1"}) as resp:
                    if resp.status != 200:
                        raise APIError("HTTP code is not 200; got {}".format(resp.status))
                    soup = BeautifulSoup(await resp.text(), "html.parser")
                    if soup.response and soup.response.error:
                        raise APIError(str(soup.response.error.contents[0]))
                    name = str(soup.profile.steamid.contents[0]).strip()
                    if name == "": name = None
                    return SteamProfile(
                        SteamID.from_64(str(soup.profile.steamid64.contents[0])),
                        name,
                        str(soup.profile.onlinestate.contents[0]) if soup.profile.onlinestate else None,
                        str(soup.profile.privacystate.contents[0]) if soup.profile.privacystate else None,
                        str(soup.profile.avatarfull.contents[0]) if soup.profile.avatarfull else None,
                        str(soup.profile.vacbanned.contents[0]) == "1" if soup.profile.vacbanned else False,
                    )
            except aiohttp.errors.ClientConnectionError as e:
                raise APIError("Connection error")


async def fetch_steam_id(name):
    try:
        return (await SteamCommunity().steam_profile(name, id64=False)).id
    except APIError as e:
        raise CommandError(str(e))


async def parse_steam_id(s):
    m = COMMUNITY_URL_ID_PATTERN.search(s)
    if m:
        return SteamID.from_64(m.group(1))

    m = COMMUNITY_URL_NAME_PATTERN.search(s)
    if m:
        return await fetch_steam_id(m.group(1))

    m = ID_TEXT_PATTERN.search(s)
    if m:
        return SteamID.from_text(m.group(1))

    m = ID_64_PATTERN.search(s)
    if m:
        return SteamID.from_64(m.group(1))

    m = ID_NAME_PATTERN.search(s)
    if m:
        return await fetch_steam_id(m.group(1))

    raise CommandError("Could not parse the given steam ID")
