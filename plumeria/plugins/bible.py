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
    lines = []
    for verse_unit in doc.passage.content.find_all('verse-unit'):
        num = int(verse_unit.find('verse-num').text)
        woc = verse_unit.find('woc')
        if woc:
            text = woc.text
        else:
            text = "".join([str(node) for node in verse_unit.children
                            if isinstance(node, NavigableString) and not isinstance(node, Comment)])
        lines.append("({}) {}".format(num, text.strip()))
    return "\n".join(lines)
