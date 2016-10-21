"""Render ASCII art from text."""

from pyfiglet import Figlet
from plumeria.command import commands, CommandError
from plumeria.message import Response
from plumeria.util.ratelimit import rate_limit

MAX_LENGTH = 20


@commands.create('figlet', category='Fun')
@rate_limit(burst_size=2)
async def figlet(message):
    """
    Generates ASCII art from text.

    Example::

        /figlet rationale.

    Response::

                       __  _                   __
           _________ _/ /_(_)___  ____  ____ _/ /__
          / ___/ __ `/ __/ / __ \/ __ \/ __ `/ / _ \\
         / /  / /_/ / /_/ / /_/ / / / / /_/ / /  __/
        /_/   \__,_/\__/_/\____/_/ /_/\__,_/_/\___(_)

    """
    text = message.content.strip()
    if len(text):
        f = Figlet(font='slant')
        return Response("```\n.\n{}```".format(f.renderText(text[:MAX_LENGTH])))
    else:
        raise CommandError("No text provided!")


def setup():
    commands.add(figlet)
