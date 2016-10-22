import asyncio
import logging
from typing import Sequence

from plumeria.command import Command, Mapping
from plumeria.core.storage import pool, migrations
from plumeria.transport import Server
from plumeria.util.collections import tree

__requires__ = ['plumeria.core.storage']

logger = logging.getLogger(__name__)


class Alias:
    """Holds an alias."""

    def __init__(self, transport: str, server: str, alias: str, command: str):
        self.transport = transport
        self.server = server
        self.alias = alias
        self.command = command


class AliasManager:
    """
    Keeps an in-memory cache of aliases.

    Aliases have to be loaded for a particular server for aliases to be available.

    """

    def __init__(self):
        self.aliases = tree()
        self.load_queue = set()
        self.load_scheduled = False

    async def initialize(self):
        await migrations.migrate("alias", __name__)

    def _put_alias(self, alias: Alias):
        self.aliases[alias.transport.lower()][alias.server.lower()][alias.alias.lower()] = alias

    def _delete_alias(self, alias: Alias):
        del self.aliases[alias.transport.lower()][alias.server.lower()][alias.alias.lower()]

    def get(self, server: Server, name: str) -> Alias:
        """Get a particular alias. Aliases for the server must have been previously loaded."""

        keys = (server.transport.id.lower(), server.id.lower(), name.lower())
        node = self.aliases
        for key in keys:
            if key in node:
                node = node[key]
            else:
                return None
        return node

    def get_all(self, server: Server) -> Sequence[Alias]:
        """Get all defined aliases for a server."""

        keys = (server.transport.id.lower(), server.id.lower())
        node = self.aliases
        for key in keys:
            if key in node:
                node = node[key]
            else:
                return []
        return node.values()

    def get_mappings(self, server_id):
        mappings = []

        for transport_aliases in self.aliases.values():
            if server_id in transport_aliases:
                for alias in transport_aliases[server_id].values():
                    mappings.append(Mapping([alias.alias],
                                            Command(None, category="(Server-Specific)", description=alias.command,
                                                    help=alias.command)))
        return mappings

    async def load(self, server: Server):
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT transport, server, alias, command "
                    "FROM alias_aliases "
                    "WHERE transport = %s AND server = %s",
                    (server.transport.id, server.id))
                for row in await cur.fetchall():
                    self._put_alias(Alias(*row))

    async def create(self, server: Server, name: str, command: str):
        alias = Alias(server.transport.id, server.id, name, command)
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "REPLACE INTO alias_aliases "
                    "(transport, server, alias, command) "
                    "VALUES "
                    "(%s, %s, %s, %s)",
                    (alias.transport, alias.server, alias.alias, alias.command))
        self._put_alias(alias)

    async def delete(self, alias: Alias):
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM alias_aliases "
                    "WHERE transport = %s AND server = %s AND alias = %s",
                    (alias.transport, alias.server, alias.alias))
        self._delete_alias(alias)

    async def load_soon(self, server: Server):
        self.load_queue.add(server)
        if not self.load_scheduled:
            asyncio.get_event_loop().create_task(self._load_background())
            self.load_scheduled = True

    async def _load_background(self):
        try:
            while len(self.load_queue):
                await asyncio.sleep(1)
                queue = set(self.load_queue)  # copy in case of change
                self.load_queue = set()

                for server in queue:
                    logger.debug("Loading aliases for transport '{}', server '{}' ({})..."
                                 .format(server.transport.id, server.name, server.id))
                    await self.load(server)
        finally:
            self.load_scheduled = False
