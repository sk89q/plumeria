import logging

from plumeria.core.storage import pool, migrations
from plumeria.core.user_prefs.manager import PreferencesManager
from plumeria.core.user_prefs.storage import DatabasePreferences
from plumeria.event import bus

__requires__ = ['plumeria.core.storage']

logger = logging.getLogger(__name__)

prefs_manager = PreferencesManager()


async def setup():
    provider = DatabasePreferences(pool, migrations)
    await provider.initialize()
    prefs_manager.provider = provider
