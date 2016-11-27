"""Stores configuration in the database."""

import logging
from typing import Sequence

from plumeria.core.storage import migrations
from plumeria.transport import Server
from plumeria.core.scoped_config.manager import ScopedConfigProvider, ScopedValue

logger = logging.getLogger(__name__)


class DatabaseConfig(ScopedConfigProvider):
    def __init__(self, pool):
        self.pool = pool

    async def init(self):
        await migrations.migrate("config", __name__)

    async def get_all(self, server: Server) -> Sequence[ScopedValue]:
        results = []
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT transport, server, channel, section, `key`, value "
                    "FROM config_values "
                    "WHERE transport = %s AND server = %s",
                    (server.transport.id, server.id))
                for row in await cur.fetchall():
                    row = list(row)
                    if not len(row[2]):
                        row[2] = None
                    results.append(ScopedValue(*row))
        return results

    async def save(self, sv: ScopedValue):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "REPLACE INTO config_values "
                    "(transport, server, channel, section, `key`, value) "
                    "VALUES "
                    "(%s, %s, %s, %s, %s, %s)",
                    (sv.transport, sv.server, sv.channel if sv.channel is not None else "", sv.section, sv.key,
                     sv.value))

    async def delete(self, sv: ScopedValue):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM config_values "
                    "WHERE transport = %s AND server = %s AND channel = %s AND section = %s AND `key` = %s",
                    (sv.transport, sv.server, sv.channel if sv.channel is not None else "", sv.section, sv.key))
