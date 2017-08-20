"""Keeps track of a queue of things to play in voice."""

import asyncio
import logging
from typing import Optional

from sortedcontainers import SortedListWithKey

from plumeria import config
from plumeria.command import CommandError
from plumeria.core.scoped_config import scoped_config
from plumeria.transport import Channel
from plumeria.transport import Server

log = logging.getLogger(__name__)

volume_default = config.create("voice_queue", "volume_default", type=float, fallback=40, scoped=True, private=False,
                               comment="The default volume level of the played audio")
queue_size = config.create("voice_queue", "queue_size", type=int, fallback=10, scoped=True, private=False,
                           comment="The number of entries that can be queued")
queue_max = config.create("voice_queue", "queue_max", type=int, fallback=20,
                          comment="The maximum queue size that will be allowed")


class EntryMeta:
    def __init__(self, title: Optional[str] = None, description: Optional[str] = None, url: Optional[str] = None):
        self.title = title
        self.description = description
        self.url = url

    def __str__(self):
        if self.title:
            return self.title
        elif self.url:
            return self.url
        else:
            return "Unknown"


class QueueEntry:
    """An individual queue entry."""

    def __init__(self, queue: 'Queue', factory, priority: int, meta: EntryMeta):
        self.queue = queue
        self.priority = priority
        self.factory = factory
        self._player = None
        self._attempted_factory = False
        self._started = False
        self.active = True
        self.meta = meta

    async def _get_player(self):
        if self._player is None:
            self._player = await self.factory(self)
            self._player.volume = self.queue.volume
        return self._player

    async def _start(self) -> bool:
        if not self.active:
            return False
        try:
            if self._started:
                (await self._get_player()).resume()
            else:
                self._started = True
                (await self._get_player()).start()
            return True
        except Exception as e:
            logging.warning("Failed to start player", exc_info=True)
            return False

    async def _stop(self) -> None:
        self.active = False
        try:
            (await self._get_player()).stop()
        except Exception as e:
            logging.warning("Failed to stop player", exc_info=True)

    async def _pause(self) -> bool:
        try:
            (await self._get_player()).pause()
            return True
        except Exception as e:
            logging.warning("Failed to pause player", exc_info=True)
            return False

    def _update_volume(self):
        if self._player:
            self._player.volume = self.queue.volume

    def on_end(self):
        self.active = False
        self.queue.handle_end(self)


class Queue:
    """
    Manages a list of things to play, with support for priorities and playback preemption.
    """

    DEFAULT_PRIORITY = 0

    def __init__(self):
        self.queue = SortedListWithKey(key=lambda item: item.priority, load=100)
        self.active = None
        self.loop = asyncio.get_event_loop()
        self._volume = 1

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, volume):
        if volume < 0:
            volume = 0
        elif volume > 100:
            volume = 1
        elif volume > 1:
            volume = volume / 100
        else:
            volume = float(volume)
        self._volume = volume
        if self.active:
            self.active._update_volume()

    def entries(self):
        return list(self.queue)

    async def add(self, factory, *, channel, priority: int = DEFAULT_PRIORITY, meta: EntryMeta):
        max_size = min(scoped_config.get(queue_size, channel), queue_max())
        if len(self.queue) >= max_size:
            raise CommandError("The queue has reached the max size of {}.".format(max_size))
        entry = QueueEntry(self, factory, priority, meta)
        self.queue.add(entry)
        await self.check_current()
        return entry

    async def skip(self, index: int = 0):
        try:
            top = self.queue[index]
            del self.queue[index]
        except IndexError:
            return False
        await self.check_current()
        return top

    async def skip_all(self, *, all: bool = False, name: Optional[str] = None):
        skipped = []
        i = 0
        while i < len(self.queue):
            remove = False

            if all:
                remove = True
            elif name is not None and name.lower() in str(self.queue[i].meta).lower():
                remove = True

            if remove:
                skipped.append(self.queue)
                del self.queue[i]
            else:
                i += 1
        await self.check_current()
        return skipped

    async def check_current(self):
        # just check if the active one is still in the queue
        if self.active:
            try:
                self.queue.index(self.active)
            except ValueError:
                await self.active._stop()
                self.active = None

        while True:
            try:
                top = self.queue[0]

                if self.active == top:
                    break  # already playing something
                elif self.active is not None and self.active != top:
                    # we have a higher priority stream incoming
                    if not await self.active._pause():
                        break  # well we can't pause this player

                self.active = top
                if await top._start():
                    break  # we started playing something!
                else:
                    del self.queue[0]
                    self.active = None
                    # loop around and try again
            except IndexError:
                break  # no more entries!!

    def handle_end(self, entry: QueueEntry):
        asyncio.run_coroutine_threadsafe(self._handle_end(entry), self.loop)

    async def _handle_end(self, entry: QueueEntry):
        try:
            top = self.queue[0]
            if top == entry:
                del self.queue[0]
        except IndexError:
            pass  # well I guess it wasn't supposed to stop
        if self.active == entry:
            self.active = None
        await self.check_current()


class QueueMap:
    """Keeps track of Queue instances, one per channel/server."""

    def __init__(self):
        self.map = {}

    def get(self, channel: Channel) -> Queue:
        """
        Get the queue for a particular channel.

        Parameters
        ----------
        channel : Channel
            The channel instance

        Returns
        -------
        Queue
            A queue instance

        """
        try:
            return self.map[channel.server.perma_id]
        except KeyError:
            volume = scoped_config.get(volume_default, channel)
            queue = Queue()
            queue.volume = volume
            self.map[channel.server.perma_id] = queue
            return queue


queue_map = QueueMap()


def setup():
    config.add(volume_default)
    config.add(queue_size)
    config.add(queue_max)
