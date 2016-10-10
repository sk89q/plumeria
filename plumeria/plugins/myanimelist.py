import aiohttp
from bs4 import BeautifulSoup

from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.util import http
from plumeria.util.message import strip_html
from plumeria.util.ratelimit import rate_limit

username = config.create("myanimelist", "username", fallback="",
                         comment="Account username for API requests on myanimelist.net")

password = config.create("myanimelist", "password", fallback="",
                         comment="Account password for API requests on myanimelist.net")


@commands.register("anime", category="Search")
@rate_limit()
async def random_user(message):
    """
    Gets information about an anime using myanimelist.net.

    Example::

        /anime code geass

    """
    query = message.content.strip()
    if not len(query):
        raise CommandError("Supply the name of an anime to search.")
    auth = aiohttp.BasicAuth(username(), password())
    r = await http.get("https://myanimelist.net/api/anime/search.xml", params=[
        ('q', query)
    ], auth=auth)
    doc = BeautifulSoup(r.text(), features="lxml")
    entries = doc.anime.find_all("entry", recursive=False)
    if not len(entries):
        raise CommandError("No results found.")
    entry = entries[0]
    return "{image}\n\n" \
           "**{name}** ({type})\n\n" \
           "**Score:** {score}\n" \
           "**Episodes:** {ep_count}\n" \
           "**Air Dates:** {start}-{end}\n\n" \
           "{synopsis}\n".format(
        image=entry.image.text,
        type=entry.type.text,
        name=entry.title.text,
        score=entry.score.text,
        ep_count=entry.episodes.text,
        start=entry.start_date.text,
        end=entry.end_date.text,
        synopsis=strip_html(entry.synopsis.text),
    )
