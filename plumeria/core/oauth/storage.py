"""Store OAuth credentials into the database."""

import logging

from .manager import TokenStore, Authorization

logger = logging.getLogger(__name__)


class DatabaseTokens(TokenStore):
    def __init__(self, pool, migrations):
        self.pool = pool
        self.migrations = migrations

    async def initialize(self):
        await self.migrations.migrate("oauth", __name__)

    async def get(self, endpoint_name: str, transport: str, user: str):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT access_token, token_type, expiration_at, refresh_token "
                    "FROM oauth_tokens "
                    "WHERE transport = %s AND user = %s AND endpoint = %s",
                    (transport, user, endpoint_name))
                row = await cur.fetchone()
                if row:
                    return Authorization(endpoint_name, transport, user, *row)
                else:
                    return None

    async def remove(self, endpoint_name: str, transport: str, user: str):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM oauth_tokens "
                    "WHERE transport = %s AND user = %s AND endpoint = %s",
                    (transport, user, endpoint_name))

    async def put(self, auth: Authorization):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "REPLACE INTO oauth_tokens "
                    "(transport, user, endpoint, access_token, token_type, expiration_at, refresh_token) "
                    "VALUES "
                    "(%s, %s, %s, %s, %s, %s, %s)",
                    (auth.transport, auth.user, auth.endpoint_name, auth.access_token, auth.token_type,
                     auth.expiration_at,
                     auth.refresh_token))
