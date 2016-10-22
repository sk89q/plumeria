import logging

from plumeria.event import bus
from plumeria.storage import pool

from .manager import ScopedConfig
from .storage import DatabaseConfig

logger = logging.getLogger(__name__)

scoped_config = ScopedConfig()


def setup():
    db_config = DatabaseConfig(pool)

    @bus.event('preinit')
    async def preinit():
        logger.info("Setting {} as the default store for scoped configuration".format(__name__))
        scoped_config.provider = db_config

    @bus.event('init')
    async def init():
        await db_config.init()
