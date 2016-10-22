"""Create new commands that call existing commands."""

import io
import json

from plumeria.command import commands, Context, CommandError, channel_only
from plumeria.event import bus
from plumeria.message import ProxyMessage, Message, Response, MemoryAttachment
from plumeria.perms import server_admins_only
from plumeria.util.format import escape_markdown
from .manager import AliasManager

__requires__ = ['plumeria.core.storage']

aliases = AliasManager()


@commands.create('alias', 'alias create', cost=4, category='Alias')
@channel_only
@server_admins_only
async def alias(message):
    """
    Creates a new command alias, which can be triggered by any other user and run under the context of
    the user that called the alias. Aliases can be updated or removed. Aliases also show up on this
    help page.

    Example::

        /alias serverinfo a2squery example.com:27015

    If commands need to be piped, escape the pipe symbol with a ^::

        /alias example echo flight simulator ^| drawtext
    """
    parts = message.content.split(" ", 1)
    if len(parts) == 2:
        await aliases.create(message.channel.server, parts[0], parts[1])
        return "Created the command alias *{}*.".format(parts[0])
    else:
        raise CommandError("<alias> <command>")


@commands.create('alias delete', 'alias remove', cost=4, category='Alias')
@channel_only
@server_admins_only
async def delete_alias(message: Message):
    """
    Deletes an alias by name.

    Example::

        /alias delete aesthetic
    """
    name = message.content.strip()
    if len(name):
        alias = aliases.get(message.server, name)
        if alias:
            await aliases.delete(alias)
            return "Deleted the command alias *{}*.".format(message.content)
        else:
            raise CommandError("That alias '{}' doesn't exist".format(name))
    else:
        raise CommandError("<alias>")


@commands.create('alias get', 'alias info', cost=4, category='Alias')
@channel_only
async def get_alias(message: Message):
    """
    Gets an alias's command.

    Example::

        /alias get aesthetic
    """
    name = message.content.strip()
    if len(name):
        alias = aliases.get(message.server, name)
        if alias:
            return "```\n{}\n```".format(escape_markdown(alias.command))
        else:
            raise CommandError("That alias '{}' doesn't exist".format(name))
    else:
        raise CommandError("<alias>")


@commands.create('alias export', cost=4, category='Alias')
@channel_only
@server_admins_only
async def export_aliases(message: Message):
    """
    Exports all aliases as a .json file that can't be imported anywhere yet.

    Example::

        /alias export
    """
    data = {}
    for alias in aliases.get_all(message.server):
        data[alias.alias] = alias.command
    return Response("Here are all the aliases on this channel", attachments=[
        MemoryAttachment(io.BytesIO(json.dumps(data).encode('utf-8')), 'aliases.json', 'application/json'),
    ])


async def setup():
    await aliases.initialize()

    @bus.event('server.ready')
    async def server_available(server):
        await aliases.load_soon(server)

    @commands.enumerator
    async def alias_enumerator(server_id):
        if server_id:
            return aliases.get_mappings(server_id)
        else:
            return []

    @commands.intercept
    async def alias_listener(original, alias, depth):
        if not original.channel.is_private:  # public channels only
            alias = aliases.get(original.channel.server, alias)
            if alias:
                message = ProxyMessage(original)
                message.content = alias.command
                message.registers['input'] = original
                return await commands.execute(message, Context(), expect_prefix=False)
        return False

    commands.add(alias)
    commands.add(delete_alias)
    commands.add(get_alias)
    commands.add(export_aliases)
