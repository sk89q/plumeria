from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.util import http
from plumeria.util.ratelimit import rate_limit

api_key = config.create("rubygems", "key",
                        fallback="",
                        comment="An API key from RubyGems.org (make an account, edit your profile)")


@commands.register("rubygems", "gems", category="Development")
@rate_limit()
async def gems(message):
    """
    Search the RubyGems repository for a package.

    Example::

        /gems discord

    Response::

        \u2022 discordrb (2.1.3) - A Ruby implementation of the[...]
        \u2022 lita-discord (0.1.1) - A Discord adapter for Lit[...]
        \u2022 omniauth-discord (0.1.3) - Discord OAuth2 Strate[...]
        \u2022 rediscord (1.0.0) - keep record id sync with dyn[...]

    """
    q = message.content.strip()
    if not q:
        raise CommandError("Search term required!")
    r = await http.get("https://rubygems.org/api/v1/search.json", params=[
        ('query', q),
    ], headers=[
        ('Authorization', api_key())
    ])
    data = r.json()
    if len(data):
        return "\n".join(map(lambda e:
                             "\u2022 **{name}** ({version}) - {desc} <{url}>".format(
                                 name=e['name'],
                                 version=e['version'],
                                 desc=e['info'],
                                 url=e['project_uri']),
                             data))
    else:
        raise CommandError("no results found")
