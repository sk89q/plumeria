from plumeria.command import commands, channel_only
from plumeria.message import Response


@commands.register('roles', category='Discord')
@channel_only
async def roles(message):
    """
    Gets the roles in the current server, including their name and ID. Intended for development purposes.

    Example::

        /roles

    Response::

        bot (160143463784458624), admin (160143463784458624)
    """
    roles = filter(lambda r: r.name != "@everyone", message.channel.server.roles)
    return Response(", ".join(["{} ({})".format(r.name, r.id) for r in roles]))


@commands.register('user id', 'userid', category='Discord')
async def userid(message):
    """
    Gets your own Discord user ID for development purposes.

    Example::

        /userid

    Response::

        43463109290000434
    """
    return Response(message.author.id)
