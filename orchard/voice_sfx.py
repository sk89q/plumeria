import logging
import os

from plumeria.command import commands, channel_only, CommandError
from plumeria.command.parse import SafeFilename
from plumeria.core.voice_queue import queue_map, QueueEntry, EntryMeta
from plumeria.util.voice import get_voice_client

__requires__ = ['plumeria.core.voice_queue']

SFX_PATH = os.path.join("sfx")
SFX_EXTS = {'.wav', '.mp3', '.mp4', '.ogg', '.m4a', '.flac'}

log = logging.getLogger(__name__)


def get_sfx_names():
    names = []
    for filename in os.listdir(SFX_PATH):
        name, ext = os.path.splitext(filename)
        if ext.lower() in SFX_EXTS:
            names.append(name)
    return names


def find_sfx(expected):
    try:
        for filename in os.listdir(SFX_PATH):
            name, ext = os.path.splitext(filename)
            if ext.lower() in SFX_EXTS and expected.lower() == name.lower():
                return os.path.abspath(os.path.join(SFX_PATH, filename))
        raise CommandError("Couldn't find the effect '{}'.".format(expected))
    except FileNotFoundError:
        raise CommandError("There isn't even a sound effect folder.")


@commands.create('sfx list', 'effect list', 'fx list', cost=2, category='Player', params=[])
@channel_only
async def sfx_list(message):
    """
    Gets a list of usable SFX.

    """
    names = get_sfx_names()
    if not len(names):
        raise CommandError("No SFX available.")
    return " ".join(names)


@commands.create('sfx', 'effect', 'fx', category='Player', params=[SafeFilename("name")])
@channel_only
async def sfx(message, name):
    """
    Plays a sound effect, which will play immediately even if there is music
    playing. (Sound effects preempt other queued items.)

    Example::

        /sfx drums

    """
    path = find_sfx(name)

    # get the voice channel
    voice_client = await get_voice_client(message.author)
    queue = queue_map.get(voice_client.channel)

    # queue that stuff up
    async def factory(entry: QueueEntry):
        return voice_client.create_ffmpeg_player(path, after=entry.on_end)

    meta = EntryMeta(title="SFX: {}".format(name))
    entry = await queue.add(factory, channel=voice_client.channel, meta=meta, priority=-1)

    # tell the user
    entries = queue.entries()
    index = entries.index(entry)
    if index == 0:
        return "Now playing **{}**...".format(meta)
    else:
        return "Queued **{}** at position #{} for play.".format(meta, index)


def setup():
    commands.add(sfx)
    commands.add(sfx_list)
