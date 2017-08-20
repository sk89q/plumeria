import asyncio
import functools
import logging
import re

import youtube_dl
from youtube_dl import DownloadError

from plumeria import config
from plumeria.command import CommandError
from plumeria.command import commands, channel_only
from plumeria.command.parse import Text
from plumeria.core.voice_queue import queue_map, QueueEntry, EntryMeta
from plumeria.util.voice import get_voice_client

__requires__ = ['plumeria.core.voice_queue']

log = logging.getLogger(__name__)

LINK_PATTERN = re.compile("((https?)://[^\s/$.?#<>].[^\s<>]*)", re.I)

source_address = config.create("voice_player", "source_address", fallback="",
                               comment="Source address for youtube_dl")


@commands.create('join voice', category='Player', params=[])
@channel_only
async def join(message):
    """
    Have the bot join the voice channel that you are in.

    Example::

        /join voice

    """
    voice_client = await get_voice_client(message.author, move_to=True, any_channel=True)
    return "I'm in {}".format(voice_client.channel.mention)


@commands.create('play', category='Player', params=[Text("url")])
@channel_only
async def play(message, url):
    """
    Play a URL.

    Example::

        /play https://www.youtube.com/watch?v=U9DZkj8Rq6g

    """

    m = LINK_PATTERN.search(url)
    if not m:
        raise CommandError("You need to provide a URL to play.")
    url = m.group(1)

    # check to see if we can play this URL
    opts = {
        'format': 'webm[abr>0]/bestaudio/best',
        'prefer_ffmpeg': True,
        'source_address': source_address(),
        'noplaylist': True,
    }
    ydl = youtube_dl.YoutubeDL(opts)
    func = functools.partial(ydl.extract_info, url, download=False)
    try:
        info = await asyncio.get_event_loop().run_in_executor(None, func)

        # get metadata
        is_twitch = 'twitch' in url
        if is_twitch:
            # twitch has 'title' and 'description' sort of mixed up
            title = info.get('description')
            description = None
        else:
            title = info.get('title')
            description = info.get('description')
    except DownloadError as e:
        raise CommandError("Can't play <{}>. It might not be a supported site.".format(url))

    # get the voice channel
    voice_client = await get_voice_client(message.author)
    queue = queue_map.get(voice_client.channel)

    # queue that stuff up
    async def factory(entry: QueueEntry):
        return await voice_client.create_ytdl_player(url, ytdl_options=opts, after=entry.on_end,
                                                     options=['-af', 'loudnorm=I=-16:TP=-1.5:LRA=11'])

    meta = EntryMeta(title=title, description=description, url=url)
    entry = await queue.add(factory, channel=voice_client.channel, meta=meta)

    # tell the user
    entries = queue.entries()
    index = entries.index(entry)
    if index == 0:
        return "Now playing **{}**...".format(meta)
    else:
        return "Queued **{}** at position #{} for play.".format(meta, index)


def setup():
    config.add(source_address)
    commands.add(join)
    commands.add(play)
