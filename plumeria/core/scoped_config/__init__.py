import logging

from plumeria.core.storage import pool
from .manager import ScopedConfig, ScopedValue
from .storage import DatabaseConfig

__requires__ = ['plumeria.core.storage']

logger = logging.getLogger(__name__)

scoped_config = ScopedConfig()


async def setup():
    db_config = DatabaseConfig(pool)
    await db_config.init()
    scoped_config.provider = db_config
