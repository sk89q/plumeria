"""Command to get the bot's changelog by running git log on the current working directory."""

import asyncio
from asyncio.subprocess import PIPE

from plumeria.command import commands
from plumeria.perms import owners_only


async def get_git_log():
    proc = await asyncio.create_subprocess_exec('git', 'log', '--oneline', '--abbrev-commit', '--all', '--graph',
                                                '--decorate', stdin=PIPE, stdout=PIPE, stderr=PIPE)
    (stdout, stderr) = await proc.communicate()
    if proc.returncode == 0:
        return stdout.decode('utf-8', 'ignore').strip().splitlines()
    else:
        return "unknown"


@commands.create('changelog', category='Utility')
@owners_only
async def changelog(message):
    """
    Grab the bot's changelog, derived from the Git repo.

    Example::

        changelog
    """
    log = await get_git_log()
    return "```{}```".format("\n".join(log[:10]))


def setup():
    commands.add(changelog)
