"""Utility functions to work with embeds."""

from plumeria.command import commands
from plumeria.message import Response
from plumeria.message.mappings import parse_mapping
from plumeria.transport.embed import Embed
from plumeria.util.ratelimit import rate_limit


@commands.create('embedify mapping', cost=2, category='Utility')
@rate_limit()
async def embedify_mapping(message):
    """
    Attempt to make a message into an embed.

    """
    mapping = parse_mapping(message.content)
    embed = Embed()
    for key, value in mapping:
        embed.add_field(name=key, value=value, inline=True)
    return Response('', embed=embed)


def setup():
    commands.add(embedify_mapping)
