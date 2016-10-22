"""Commands to work with time and date."""

import time

from plumeria.command import commands
from plumeria.message import Response


@commands.create('timestamp', category='Utility')
async def timestamp(message):
    """
    Gets the current UNIX timestamp.
    """
    return Response(str(int(time.time())))


def setup():
    commands.add(timestamp)
