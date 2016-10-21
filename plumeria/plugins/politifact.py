"""Query Politifact.com to check the veracity of recent statements."""

import re

import plumeria.util.http as http
from plumeria.command import commands, CommandError
from plumeria.command.parse import Text
from plumeria.message.mappings import build_mapping
from plumeria.util.collections import SafeStructure
from plumeria.util.ratelimit import rate_limit


@commands.create("politifact", "fact check", category="Search", params=[Text('name')])
@rate_limit()
async def politifact(message, name):
    """
    Fact check for recently said/checked statements by a person.

    Example::

        fact check barack obama

    """
    name_dashed = re.sub(" +", "-", name.lower())
    r = await http.get("http://www.politifact.com/api/statements/truth-o-meter/people/{}/json/".format(name_dashed),
                       params={
                           "n": 20,
                       })

    results = SafeStructure(r.json())

    if not results:
        raise CommandError("No results found. Either the person isn't fact checked by politifact.com, you "
                           "didn't write the person's entire name, or you misspelled the name.")

    return build_mapping(
        [(e.ruling.ruling, "{} ({})".format(e.ruling_headline, e.statement_context)) for e in results[:10]])


def setup():
    commands.add(politifact)
