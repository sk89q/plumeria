import collections

import rethinkdb as r

from plumeria.command import commands, Command, Context, CommandError, Mapping, channel_only
from plumeria.event import bus
from plumeria.message import ProxyMessage, Response
from plumeria.perms import server_admins_only
from plumeria.rethinkdb import pool, migrations


@bus.event('preinit')
async def preinit():
    async def initial(conn):
        await r.table_create("aliases").run(conn)
        await r.table("aliases").index_create("server_id_alias", [r.row["server_id"], r.row["alias"]]).run(conn)

    await migrations.migrate("alias",
                             (("initial", initial), ))


class AliasManager:
    def __init__(self):
        self.aliases = collections.defaultdict(lambda: {})

    async def load(self):
        self.aliases.clear()
        async with pool.acquire() as conn:
            cursor = await r.table("aliases").run(conn)
            while await cursor.fetch_next():
                row = await cursor.next()
                self.aliases[row['server_id']][row['alias']] = row['command']

    async def create(self, server, alias, command):
        alias = alias.lower()
        id = "{}_{}".format(server.id, alias)
        async with pool.acquire() as conn:
            await r.table("aliases").get(id).replace({
                "id": id,
                "server_id": server.id,
                "alias": alias,
                "command": command}).run(conn)
        self.aliases[server.id][alias] = command

    async def delete(self, server, alias):
        alias = alias.lower()
        async with pool.acquire() as conn:
            await r.table("aliases").filter(id == "{}_{}".format(server.id, alias)).delete().run(conn)
        if alias in self.aliases[server.id]:
            del self.aliases[server.id][alias]

    def match_command(self, message, command):
        if command in self.aliases[message.channel.server.id]:
            return self.aliases[message.channel.server.id][command]
        return None

    def get_mappings(self, server_id):
        if server_id in self.aliases:
            mappings = []
            for alias, command in self.aliases[server_id].items():
                mappings.append(
                    Mapping([alias], Command(None, category="(Server-Specific)", description=command, help=command)))
            return mappings
        else:
            return []


aliases = AliasManager()


@bus.event('init')
async def init():
    await aliases.load()


@commands.register('echo', cost=0.2, category="Utility")
async def echo(message):
    """
    Simply returns the input string.

    Can be used to create an alias::

        /alias website echo Our website is http://example.com
    """
    return Response(message.content)


@commands.register('alias', cost=4, category='Alias')
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
        await message.respond("Created the command alias *{}*.".format(parts[0]))
    else:
        raise CommandError("<alias> <command>")


@commands.register('alias delete', cost=4, category='Alias')
@channel_only
@server_admins_only
async def delete_alias(message):
    """
    Deletes an alias by name.

    Example::

        /alias delete aesthetic
    """
    if len(message.content):
        await aliases.delete(message.channel.server, message.content)
        await message.respond("Deleted the command alias *{}*.".format(message.content))
    else:
        raise CommandError("<alias>")


@commands.enumerator
async def alias_enumerator(server_id):
    if server_id:
        return aliases.get_mappings(server_id)
    else:
        return []


@commands.intercept
async def alias_listener(message, value, depth):
    if not message.channel.is_private:  # public channels only
        value = aliases.match_command(message, value)
        if value:
            message = ProxyMessage(message)
            message.content = value
            return await commands.execute(message, Context(), expect_prefix=False)
        return False
