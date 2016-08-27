from bs4 import BeautifulSoup

from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.util import http
from plumeria.util.message import escape_markdown
from plumeria.util.ratelimit import rate_limit

api_key = config.create("wolfram", "key",
                        fallback="",
                        comment="An API key from http://products.wolframalpha.com/api/")


@commands.register("wolfram", category="Search")
@rate_limit()
async def wolfram(message):
    """
    Looks up information about a topic with Wolfram Alpha.

    Example::

        /wolfram 2+50
        /wolfram Integrate[4x^2,x]
        /wolfram pi

    Response::

        Decimal approximation: 3.14159265358...
        Property: pi is a transcendental number
        Continued fraction: [3; 7, 15, 1, 292, [...]

    """
    q = message.content.strip()
    if not q:
        raise CommandError("Search term required!")
    r = await http.get("http://api.wolframalpha.com/v2/query", params=[
        ('input', q),
        ('appid', api_key()),
    ])
    doc = BeautifulSoup(r.text(), features="lxml")
    pods = doc.queryresult.find_all("pod", recursive=False)
    if len(pods):
        lines = []
        for pod in pods:
            if pod.get("id", "") != "Input":
                for node in pod.find_all("plaintext"):
                    line = (' '.join(node.stripped_strings)).strip()
                    if len(line):
                        lines.append("**{}:** {}".format(pod['title'], escape_markdown(line)))
        if len(lines):
            return "\n".join(lines[:4])
        else:
            return "no data"
    else:
        raise CommandError("no results found")
