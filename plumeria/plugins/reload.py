import asyncio
import logging
import sys
from asyncio.subprocess import PIPE

from plumeria.command import commands, CommandError
from plumeria.perms import owners_only
from plumeria.plugins.discord_transport import client

logger = logging.getLogger(__name__)


async def get_git_id():
    proc = await asyncio.create_subprocess_exec('git', 'describe', '--dirty', '--all', '--long', stdin=PIPE, stdout=PIPE, stderr=PIPE)
    (stdout, stderr) = await proc.communicate()
    if proc.returncode == 0:
        return stdout.decode('utf-8', 'ignore').strip()
    else:
        return "unknown"


@commands.register('update', category='Utility')
@owners_only
async def update(message):
    """
    Updates the bot software and restart it.

    This only works if a Git repo is setup and the bot is running from that repo.
    After a ``git pull --rebase`` completes, the bot simply quits so there
    needs to be a restart script to reboot the bot. It's also recommended
    to install dependencies listed in ``requirements.txt`` on update from
    the restart script.

    Example::

        /update
    """
    old_id = await get_git_id()
    await message.respond("Updating from {}...".format(old_id))
    proc = await asyncio.create_subprocess_exec('git', 'pull', '--rebase', stdin=PIPE, stdout=PIPE, stderr=PIPE)
    (stdout, stderr) = await proc.communicate()
    if proc.returncode == 0:
        new_id = await get_git_id()
        if new_id != old_id:
            await message.respond("Downloaded {}! Now restarting...".format(new_id))
            await client.logout()
            asyncio.get_event_loop().call_soon(sys.exit, 0)
        else:
            await message.respond("No update for the bot found.")
    else:
        raise CommandError("Update error: {}".format(stderr.decode("utf-8", "ignore")))
