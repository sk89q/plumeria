"""Commands to get statistics about the bot instance."""

from plumeria.command import commands
from plumeria.transport import transports
from plumeria.util.ratelimit import rate_limit


@commands.create("stats", "statistics", category="Search", params=[])
@rate_limit()
async def stats(message):
    """
    Get statistics for the bot, like the number of servers it is on.
    """
    transport_count = len(transports.transports)
    server_count = 0
    channel_count = 0
    member_count = 0
    member_ids = set()

    for transport in transports.transports.values():
        for server in transport.servers:
            server_count += 1
            for channel in server.channels:
                channel_count += 1
            for member in server.members:
                member_count += 1
                member_ids.add(member.id)

    return "Software: Plumeria (<https://github.com/sk89q/Plumeria>)\n" \
           "# transports: {}\n" \
           "# servers: {}\n" \
           "# channels: {}\n" \
           "# seen users: {} ({} unique) [not accurate]".format(
        transport_count,
        server_count,
        channel_count,
        member_count,
        len(member_ids),
    )


def setup():
    commands.add(stats)
