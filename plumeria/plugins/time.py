import time

from plumeria.command import commands
from plumeria.message import Response


@commands.register('timestamp', category='Utility')
async def timestamp(message):
    """
    Gets the current UNIX timestamp.
    """
    return Response(str(int(time.time())))
