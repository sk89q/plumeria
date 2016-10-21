"""Search Urban Dictionary for the definition of a word or phrase."""

from plumeria.command import commands, CommandError
from plumeria.util import http
from plumeria.util.ratelimit import rate_limit


@commands.create("urban", "urb", category="Search")
@rate_limit()
async def urban_dictionary(message):
    """
    Search Urban Dictionary for a word.

    Example::

        /urban hello

    """
    q = message.content.strip()
    if not q:
        raise CommandError("Search term required!")
    r = await http.get("http://api.urbandictionary.com/v0/define", params=[
        ('term', q),
    ])
    data = r.json()
    if len(data['list']):
        return "**{word}** - {definition}".format(
            word=data['list'][0]['word'],
            definition=data['list'][0]['definition'])
    else:
        raise CommandError("no results found")


def setup():
    commands.add(urban_dictionary)
