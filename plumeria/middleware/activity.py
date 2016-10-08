import asyncio
from datetime import datetime, timedelta

import cachetools

from plumeria.event import bus
from plumeria.message import Message
from plumeria.transport import Channel


class ActivityTracker:
    """Keeps track of who has spoken recently in a channel."""

    def __init__(self, max_size=2000, ttl=60 * 30, fetch_limit=100):
        self.ttl = ttl
        self.cache = cachetools.TTLCache(maxsize=max_size, ttl=ttl)
        self.fetched_history = cachetools.LRUCache(maxsize=300)
        self.fetch_limit = fetch_limit
        self.fetch_lock = asyncio.Lock()

    def _is_loggable(self, dt):
        return dt > datetime.now() - timedelta(seconds=self.ttl)

    def log(self, message: Message):
        if message.channel.multiple_participants:
            if self._is_loggable(message.timestamp):
                server_id = message.channel.server.id if message.channel.server else None
                key = (message.channel.transport.id, server_id, message.channel.id, message.author.id)
                self.cache[key] = message.author

    async def get_recent_users(self, channel: Channel):
        expected_key = (channel.transport.id, channel.server.id if channel.server else None, channel.id)

        if expected_key not in self.fetched_history:
            with await self.fetch_lock:
                async for message in channel.get_history(limit=self.fetch_limit):
                    self.log(message)
                self.fetched_history[expected_key] = True

        results = []
        for key, user in self.cache.items():
            if tuple(key[:3]) == expected_key:
                results.append(user)

        return results


tracker = ActivityTracker()


@bus.event("message")
async def on_message(message: Message):
    tracker.log(message)
