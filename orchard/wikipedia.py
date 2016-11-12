from plumeria.command import commands, CommandError
from plumeria.command.parse import Text
from plumeria.message.mappings import build_mapping
from plumeria.util import http
from plumeria.util.ratelimit import rate_limit


@commands.create("wikipedia", "wiki", "w", category="Search", params=[Text('query')])
@rate_limit()
async def wikipedia(message, query):
    """
    Search English Wikipedia and get an abstract.

    Example::

        w canada

    """
    r = await http.get("https://en.wikipedia.org/w/api.php", params=[
        ('action', 'opensearch'),
        ('limit', '5'),
        ('redirects', 'resolve'),
        ('format', 'json'),
        ('search', query)
    ])
    data = r.json()
    _, titles, abstracts = data[:3]
    if not len(abstracts):
        raise CommandError("No results found for '{}'".format(query))
    return build_mapping([
                             (title, abstract) for title, abstract in zip(titles, abstracts) if
                             not abstract.endswith("may refer to:")
                             ][:3])


def setup():
    commands.add(wikipedia)
