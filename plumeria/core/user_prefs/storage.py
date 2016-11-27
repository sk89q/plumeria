"""Store user preferences into the database."""

import logging
from typing import Mapping

from plumeria.core.user_prefs.manager import PreferencesProvider, Preference

from plumeria.transport import User

logger = logging.getLogger(__name__)


class DatabasePreferences(PreferencesProvider):
    def __init__(self, pool, migrations):
        self.pool = pool
        self.migrations = migrations

    async def initialize(self):
        await self.migrations.migrate("prefs", __name__)

    async def get_all(self, user: User) -> Mapping[str, str]:
        values = {}
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT name, value "
                    "FROM prefs_values "
                    "WHERE transport = %s AND user = %s",
                    (user.transport.id, user.id))
                for row in await cur.fetchall():
                    values[row[0]] = row[1]
        return values

    async def put(self, pref: Preference, user: User, value: str) -> str:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "REPLACE INTO prefs_values "
                    "(transport, user, name, value) "
                    "VALUES "
                    "(%s, %s, %s, %s)",
                    (user.transport.id, user.id, pref.name, value))

    async def get(self, pref: Preference, user: User) -> str:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT value "
                    "FROM prefs_values "
                    "WHERE transport = %s AND user = %s AND name = %s",
                    (user.transport.id, user.id, pref.name))
                row = await cur.fetchone()
                if row:
                    return row[0]
                else:
                    raise KeyError()

    async def remove(self, pref: Preference, user: User):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM prefs_values "
                    "WHERE transport = %s AND user = %s AND name = %s",
                    (user.transport.id, user.id, pref.name))
