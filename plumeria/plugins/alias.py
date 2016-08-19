import collections
import discord
from plumeria.event import bus
from plumeria.message import ProxyMessage, Response
from plumeria.command import commands, Command, Context, CommandError, Mapping, channel_only
from plumeria.perms import server_admins_only
from plumeria.storage import Session


class AliasManager:
    def __init__(self):
        self.aliases = collections.defaultdict(lambda: {})

    def load(self):
        self.aliases.clear()
        session = Session()
        try:
            for row in session.execute("SELECT server_id, alias, command FROM alias").fetchall():
                server_id, alias, command = row
                self.aliases[server_id][alias] = command
        finally:
            session.close()

    def create(self, server, alias, command):
        alias = alias.lower()
        session = Session()
        try:
            session.execute("REPLACE INTO alias (server_id, alias, command) VALUES (%s, %s, %s)",
                           [server.id, alias, command])
            session.commit()
        finally:
            session.rollback()
        self.aliases[server.id][alias] = command

    def delete(self, server, alias):
        alias = alias.lower()
        session = Session()
        try:
            session.execute("DELETE FROM alias WHERE server_id = %s AND alias = %s",
                           [server.id, alias])
            session.commit()
        finally:
            session.rollback()
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
    aliases.load()


@commands.register('echo', cost=0.2, category="Utility")
async def echo(message):
    """
    Simply returns the input string.

    Can be used to create an alias::

        alias website echo Our website is http://example.com
    """
    return Response(message.content)


@commands.register('alias', cost=4, category='Alias')
@channel_only
@server_admins_only
async def alias(message):
    """
    Creates a new command alias.

    Example::

        alias serverinfo a2squery example.com:27015

    If commands need to be piped, escape the pipe symbol with a ^::

        alias example echo flight simulator ^| drawtext
    """
    parts = message.content.split(" ", 1)
    if len(parts) == 2:
        aliases.create(message.channel.server, parts[0], parts[1])
        await message.respond("Created the command alias *{}*.".format(parts[0]))
    else:
        raise CommandError("<alias> <command>")


@commands.register('deletealias', cost=4, category='Alias')
@channel_only
@server_admins_only
async def deletealias(message):
    """
    Deletes an alias by name.
    """
    if len(message.content):
        aliases.delete(message.channel.server, message.content)
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
