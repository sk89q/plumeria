from plumeria.command import commands, channel_only
from plumeria.message import Response


@commands.register('roles', category='Discord')
@channel_only
async def roles(message):
    """
    Gets the roles in the current server, including their name and ID. Intended for development purposes.
    """
    roles = filter(lambda r: r.name != "@everyone", message.channel.server.roles)
    return Response(", ".join(["{} ({})".format(r.name, r.id) for r in roles]))


@commands.register('userid', category='Discord')
async def userid(message):
    """
    Gets your own Discord user ID for development purposes.
    """
    return Response(message.author.id)
