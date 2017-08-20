import logging
import os
import random
import re

from plumeria.command import commands, channel_only, CommandError
from plumeria.command.parse import Text
from plumeria.core.voice_queue import queue_map, QueueEntry, EntryMeta
from plumeria.core.webserver import app, render_template
from plumeria.message import Response
from plumeria.util.voice import get_voice_client

__requires__ = ['plumeria.core.voice_queue']

SFX_PATH = os.path.join("sfx")
SFX_EXTS = {'.wav', '.mp3', '.mp4', '.ogg', '.m4a', '.flac'}
STRIP_RE = re.compile("[^a-z0-9\\s]", re.I)
WORD_SPLIT_RE = re.compile("\s+")

log = logging.getLogger(__name__)


def get_words(name):
    return set(WORD_SPLIT_RE.split(STRIP_RE.sub('', name.lower()).strip()))


def get_sfx_names():
    names = []
    for filename in os.listdir(SFX_PATH):
        name, ext = os.path.splitext(filename)
        if ext.lower() in SFX_EXTS:
            names.append({
                'name': name,
                'triggers': get_words(name),
            })
    names.sort(key=lambda e: e['name'])
    return names


def find_sfx(expected):
    try:
        expected_words = get_words(expected)
        choices = []
        for filename in os.listdir(SFX_PATH):
            name, ext = os.path.splitext(filename)
            if ext.lower() in SFX_EXTS:
                words = get_words(name)
                common = words.intersection(expected_words)
                if len(common) == len(expected_words):
                    choices.append(os.path.abspath(os.path.join(SFX_PATH, filename)))
        if not len(choices):
            raise CommandError("Couldn't find the effect '{}'.".format(expected))
        return random.choice(choices)
    except FileNotFoundError:
        raise CommandError("There isn't even a sound effect folder.")


@commands.create('sfx list', 'sfxlist', cost=2, category='Player', params=[])
@channel_only
async def sfx_list(message):
    """
    Gets a list of usable SFX.

    """
    return Response(await app.get_base_url() + "/sfx-list/")


@commands.create('sfx', 'sfx play', 'sfxplay', category='Player', params=[Text("name")])
@channel_only
async def sfx(message, name):
    """
    Play a sound effect, which will play immediately even if there is music
    playing. (Sound effects preempt other queued items.)

    The search matches words, so 'hello there' would match all effects with both
    the words 'hello' and 'there' in their name. If there are multiple
    matches, a random one would be chosen.

    Example::

        /sfx drums

    """
    path = find_sfx(name)

    # get the voice channel
    voice_client = await get_voice_client(message.author)
    queue = queue_map.get(voice_client.channel)

    # queue that stuff up
    async def factory(entry: QueueEntry):
        return voice_client.create_ffmpeg_player(path, after=entry.on_end,
                                                 options=['-af', 'loudnorm=I=-16:TP=-1.5:LRA=11'])

    meta = EntryMeta(title="effect: {}".format(os.path.splitext(os.path.basename(path))[0]))
    entry = await queue.add(factory, channel=voice_client.channel, meta=meta, priority=-1)

    # tell the user
    entries = queue.entries()
    index = entries.index(entry)
    if index == 0:
        return "Now playing **{}**...".format(meta)
    else:
        return "Queued **{}** at position #{} for play.".format(meta, index)


@app.route('/sfx-list/')
async def handle(request):
    return render_template("sfx_list.html", names=get_sfx_names())


def setup():
    commands.add(sfx)
    commands.add(sfx_list)
    app.add(handle)
