from plumeria.command import CommandError
from plumeria.command import commands, channel_only
from plumeria.command.parse import Float, Text
from plumeria.core.voice_queue import queue_map
from plumeria.message.lists import build_list
from plumeria.util.voice import voice_with_bot_only

__requires__ = ['plumeria.core.voice_queue']


@commands.create('playing', category='Player', params=[])
@channel_only
async def playing(message):
    """
    Show the currently playing track.

    Example::

        /playing

    """
    queue = queue_map.get(message.channel)
    entries = queue.entries()
    if not len(entries):
        raise CommandError("Nothing is playing.")
    return str(entries[0].meta)


@commands.create('queue', category='Player', params=[])
@channel_only
async def view_queue(message):
    """
    Shows all the queued entries.

    Example::

        /queue

    Response::

        \u2022 SAINT MOTEL - "Move" (Official Video)
        \u2022 Red Hot Chili Peppers - Can't Stop Lyrics
        \u2022 The White Stripes - 'Seven Nation Army'
        \u2022 Future Islands - Ran (Official Video)

    """
    queue = queue_map.get(message.channel)
    entries = queue.entries()
    if not len(entries):
        raise CommandError("The queue is empty.")
    return build_list([str(entry.meta) for entry in entries])


@commands.create('skip', category='Player', params=[])
@channel_only
@voice_with_bot_only
async def skip(message):
    """
    Skip the currently playing track.

    Example::

        /skip

    """
    queue = queue_map.get(message.channel)
    entry = await queue.skip()
    if not entry:
        raise CommandError("Nothing to skip.")
    return "Skipped **{}**.".format(str(entry.meta))


@commands.create('undo', category='Player', params=[Text("query", fallback=None)])
@channel_only
@voice_with_bot_only
async def undo(message, query=None):
    """
    Skip the last queued track, or if a parameter is provided, skip tracks containing
    the provided phrase in the name.

    Example::

        /undo
        /undo parks

    """
    queue = queue_map.get(message.channel)
    if query:
        skipped = await queue.skip_all(name=query)
        return "Skipped **{}**.".format(len(skipped))
    else:
        count = len(queue.queue)
        if count == 0:
            raise CommandError("Queue is empty.")
        elif count == 1:
            raise CommandError("Queue only has 1 item.")
        else:
            entry = await queue.skip(count - 1)
            return "Skipped **{}**.".format(str(entry.meta))


@commands.create('clear queue', 'clearqueue', category='Player', params=[])
@channel_only
@voice_with_bot_only
async def clear_queue(message):
    """
    Completely empty the queue.

    Example::

        /clear queue

    """
    queue = queue_map.get(message.channel)
    skipped = await queue.skip_all(all=True)
    return "Removed **{}**. Queue is now empty.".format(len(skipped))


@commands.create('volume', 'set volume', category='Player', params=[Float('volume')])
@channel_only
@voice_with_bot_only
async def set_volume(message, volume: float):
    """
    Sets the volume of the player. The volume will persist until the
    bot is restarted.

    Set the ``voice_queue/volume_default`` configuration to have it be
    saved for the server.

    Example::

        /volume 80
        /volume 0.8

    """
    queue = queue_map.get(message.channel)
    queue.volume = volume
    return "Volume set!"


def setup():
    commands.add(view_queue)
    commands.add(playing)
    commands.add(skip)
    commands.add(undo)
    commands.add(clear_queue)
    commands.add(set_volume)
