"""Add an echo/say command that prints out text."""

from plumeria.command import commands
from plumeria.message import Response


@commands.create('echo', 'say', cost=0.2, category="Utility")
async def echo(message):
    """
    Simply returns the input string.

    Can be used to create an alias::

        /alias website echo Our website is http://example.com
    """
    return Response(message.content)


def setup():
    commands.add(echo)
