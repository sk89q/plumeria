import logging

from plumeria.core.user_prefs.manager import PreferencesManager
from plumeria.core.user_prefs.storage import DatabasePreferences
from plumeria.event import bus
from plumeria.storage import pool, migrations

logger = logging.getLogger(__name__)

prefs_manager = PreferencesManager()


def setup():
    provider = DatabasePreferences(pool, migrations)

    @bus.event('preinit')
    async def preinit():
        logger.info("Setting {} as the default store for user preferences".format(__name__))
        prefs_manager.provider = provider

    @bus.event('init')
    async def init():
        await provider.initialize()
