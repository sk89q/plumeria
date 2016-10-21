"""Search the PHP Packagist repository for PHP libraries."""

from plumeria.command import commands, CommandError
from plumeria.util import http
from plumeria.util.ratelimit import rate_limit


@commands.create("packagist", "composer", category="Development")
@rate_limit()
async def packagist(message):
    """
    Search the Packagist repository for a package.

    Example::

        /packagist discord

    Response::

        \u2022 laravel-notification-channels/discord - Laravel [...]
        \u2022 socialiteproviders/discord - Discord OAuth2 Prov[...]
        \u2022 team-reflex/oauth2-discord - OAuth2 client for a[...]
        \u2022 pnobbe/oauth2-discord - Discord OAuth 2.0 Client[...]

    """
    q = message.content.strip()
    if not q:
        raise CommandError("Search term required!")
    r = await http.get("https://packagist.org/search.json", params=[
        ('q', q),
    ])
    data = r.json()
    if len(data['results']):
        return "\n".join(map(lambda e:
                             "\u2022 **{name}** - {desc} <{url}>".format(
                                 name=e['name'],
                                 desc=e['description'],
                                 url=e['url']),
                             data['results']))
    else:
        raise CommandError("no results found")


def setup():
    commands.add(packagist)
