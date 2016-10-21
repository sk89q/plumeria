"""Look up upcoming music events using Songkick.com."""

import plumeria.util.http as http
from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.command.parse import Text
from plumeria.message.lists import build_list
from plumeria.plugin import PluginSetupError
from plumeria.util.collections import SafeStructure
from plumeria.util.ratelimit import rate_limit

api_key = config.create("songkick", "key",
                        fallback="",
                        comment="An API key from songkick.com (NOTE: requires approval from a Songkick employee)")


@commands.create("events", category="Music", params=[Text('artist')])
@rate_limit()
async def search_events(message, artist):
    """
    Search for upcoming events for an artist.

    Example::

        events the dear hunter

    """
    r = await http.get("http://api.songkick.com/api/3.0/events.json", params={
        "artist_name": artist,
        "apikey": api_key()
    })

    results = SafeStructure(r.json()).resultsPage.results.event

    if not results:
        raise CommandError("Artist not found or there are no upcoming scheduled events for the artist on songkick.com.")

    return build_list([
        "**{}** {}".format(event.location.city, event.displayName) for event in results[:10]
    ]) + "\n`Event information from Songkick.com`"


def setup():
    config.add(api_key)

    if not api_key():
        raise PluginSetupError("This plugin requires an API key from https://songkick.com. To obtain an API key, you "
                               "must submit an application and have it approved.")

    commands.add(search_events)
