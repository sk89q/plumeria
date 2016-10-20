from bs4 import BeautifulSoup
from bs4 import Comment
from bs4 import NavigableString

import plumeria.util.http as http
from plumeria.command import commands, CommandError
from plumeria.command.parse import Text
from plumeria.util.ratelimit import rate_limit


@commands.register("bible", "esv", category="Search", params=[Text('verse')])
@rate_limit()
async def search_esv(message, verse):
    """
    Search for a bible passage from the English Standard Version.

    Example::

        bible Romans 12:16

    """
    r = await http.get("http://www.esvapi.org/v2/rest/passageQuery", params={
        "key": "IP",
        "passage": verse,
        "output-format": "crossway-xml-1.0"
    })

    doc = BeautifulSoup(r.text(), features="lxml")
    if not doc.passage:
        raise CommandError("Verse not found.")
    if doc.passage.content.find('woc'):
        return doc.passage.content.find('woc').text
    return "".join([str(node) for node in doc.passage.content.find('verse-unit').children
                    if isinstance(node, NavigableString) and not isinstance(node, Comment)])
