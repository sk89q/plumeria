from plumeria.command import commands, CommandError
from plumeria.message.lists import build_list
from plumeria.perms import owners_only
from plumeria.transport import transports


@commands.register('join', category='Utility')
@owners_only
async def join(message):
    """
    Accept an invite to join a server.

    Example::

        /join https://discord.gg/00000

    """
    url = message.content.strip()
    results = []
    if not len(url):
        raise CommandError("Supply an invite URL.")
    for transport in transports.transports.values():
        if hasattr(transport, 'accept_invite'):
            try:
                await transport.accept_invite(url)
                results.append((transport.id, 'Success \N{WHITE HEAVY CHECK MARK}'))
            except Exception as e:
                results.append((transport.id, '\N{WARNING SIGN} {}'.format(str(e))))
        else:
            results.append((transport.id, "\N{WARNING SIGN} No support for invite links"))
    if len(results):
        return build_list(["**{}:** {}".format(e[0], e[1]) for e in results])
    else:
        raise CommandError("No transports available.")
