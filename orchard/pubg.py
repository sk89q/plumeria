"""Get stats for PLAYERUNKNOWN'S Battlegrounds."""

from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.command.parse import Word
from plumeria.message.lists import build_list
from plumeria.plugin import PluginSetupError
from plumeria.util import http
from plumeria.util.ratelimit import rate_limit

api_key = config.create("pubg_tracker_network", "key",
                        fallback="",
                        comment="A Tracker Network API key. API keys can be registered at "
                                "https://pubgtracker.com/")


@commands.create('pubg', cost=2, category='Games', params=[Word('name')])
@rate_limit()
async def pubg(message, name):
    """
    Get the stats for a user in PLAYERUNKNOWN's Battlegrounds.

    Example::

        /pubg example

    """
    r = await http.get("https://pubgtracker.com/api/profile/pc/{}".format(name), headers={
        "TRN-Api-Key": api_key()
    })
    data = r.json()

    if 'defaultSeason' not in data:
        raise CommandError("Unknown name or other error.")

    lines = []
    season = data['defaultSeason']
    for stat in data['Stats']:
        if season == stat['Season'] and stat['Region'] == 'agg':
            values = {}
            for entry in stat['Stats']:
                values[entry['field']] = entry['displayValue']
            lines.append(
                "**{type}**: Rounds: **{RoundsPlayed}** | Rating: **{Rating}** | Win: **{WinRatio}** | K/D: **{KillDeathRatio}** | Heals/g: **{HealsPg}** | "
                "Headsh/g: **{HeadshotKillsPg}** | K/g: **{KillsPg}** | Dist/g: **{MoveDistancePg}**".format(
                    type=stat['Match'].capitalize(), **values))

    if not len(lines):
        raise CommandError("No stats available / unknown name.")

    return build_list(lines)


def setup():
    config.add(api_key)

    if not api_key():
        raise PluginSetupError(
            "This plugin requires an API key from pubgtracker.com. Registration is free. Get keys from "
            "https://pubgtracker.com/.")

    commands.add(pubg)
