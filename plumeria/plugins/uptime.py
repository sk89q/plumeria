import time

from plumeria.command import commands
from plumeria.util.ratelimit import rate_limit

start = time.time()


@commands.register('uptime', category='Utility')
@rate_limit()
async def uptime(message):
    """
    Get the uptime of the server.

    """
    s = time.time() - start
    hours = s // 3600
    s -= hours * 3600
    minutes = s // 60
    seconds = s - (minutes * 60)
    return "{:.0f} hour{}, {:.0f} minute{}, {:.0f} second{}".format(hours, "s" if hours != 1 else "",
                                                                    minutes, "s" if minutes != 1 else "",
                                                                    seconds, "s" if seconds != 1 else "")
