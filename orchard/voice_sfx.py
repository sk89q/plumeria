import logging
import os
import re
from difflib import SequenceMatcher

from plumeria.command import commands, channel_only, CommandError
from plumeria.command.parse import SafeFilename
from plumeria.core.voice_queue import queue_map, QueueEntry, EntryMeta
from plumeria.util.voice import get_voice_client

__requires__ = ['plumeria.core.voice_queue']

SFX_PATH = os.path.join("sfx")
SFX_EXTS = {'.wav', '.mp3', '.mp4', '.ogg', '.m4a', '.flac'}
STRIP_RE = re.compile("[^a-z0-9]", re.I)

log = logging.getLogger(__name__)


def normalize(name):
    return STRIP_RE.sub('', name.lower())


def get_sfx_names():
    names = []
    for filename in os.listdir(SFX_PATH):
        name, ext = os.path.splitext(filename)
        if ext.lower() in SFX_EXTS:
            names.append(name)
    return names


def find_sfx(expected):
    expected_norm = normalize(expected)
    choices = []
    try:
        for filename in os.listdir(SFX_PATH):
            name, ext = os.path.splitext(filename)
            name_norm = normalize(name)
            if ext.lower() in SFX_EXTS and expected_norm in name_norm:
                ratio = SequenceMatcher(None, name_norm, expected_norm).ratio()
                choices.append((os.path.abspath(os.path.join(SFX_PATH, filename)), ratio))
        if not len(choices):
            raise CommandError("Couldn't find the effect '{}'.".format(expected))
        choices.sort(key=lambda entry: -entry[1])
        return choices[0][0]
    except FileNotFoundError:
        raise CommandError("There isn't even a sound effect folder.")


@commands.create('sfx list', 'sfxlist', cost=2, category='Player', params=[])
@channel_only
async def sfx_list(message):
    """
    Gets a list of usable SFX.

    """
    names = get_sfx_names()
    if not len(names):
        raise CommandError("No SFX available.")
    return "; ".join(names)


@commands.create('sfx', 'sfx play', 'sfxplay', category='Player', params=[SafeFilename("name")])
@channel_only
async def sfx(message, name):
    """
    Play a sound effect, which will play immediately even if there is music
    playing. (Sound effects preempt other queued items.)

    You can provide partial names: i.e. 'drum' will match 'drums'.

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

    meta = EntryMeta(title="effect: {}".format(os.path.splitext(os.path.basename(path))[0]))
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
