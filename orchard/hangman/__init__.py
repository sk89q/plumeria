import asyncio
import random
import re

import PIL
import cachetools
import pkg_resources
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from plumeria.command import CommandError
from plumeria.command import commands, channel_only
from plumeria.command.parse import Word
from plumeria.config.common import games_allowed_only
from plumeria.message import ImageAttachment, Response

with pkg_resources.resource_stream(__name__, "assets/Scribble Scrawl.ttf") as f:
    guess_font = ImageFont.truetype(f, 18)
with pkg_resources.resource_stream(__name__, "assets/Scribble Scrawl.ttf") as f:
    guessed_font = ImageFont.truetype(f, 10)
with pkg_resources.resource_stream(__name__, "assets/word_list.txt") as f:
    word_list = list(filter(len, f.read().decode('utf-8').splitlines()))

cache = cachetools.LRUCache(maxsize=1000)


class Game:
    def __init__(self, phrase: str):
        self.phrase = phrase.upper()
        self.obscured = list(re.sub("[A-Z]", "_", self.phrase))
        self.guessed = []
        self.wrong_count = 0

    def guess(self, letter: str):
        letter = letter.upper()
        if letter in self.guessed:
            raise CommandError("'{}' was already guessed!".format(letter))
        self.guessed.append(letter)
        if letter in self.phrase:
            for i, l in enumerate(self.phrase):
                if l == letter:
                    self.obscured[i] = l
        else:
            self.wrong_count += 1

    @property
    def won(self):
        return '_' not in self.obscured

    @property
    def lost(self):
        return self.wrong_count >= 6

    def create_image(self) -> PIL.Image.Image:
        with pkg_resources.resource_stream(__name__, "assets/{}.png".format(self.wrong_count)) as f:
            graphic = Image.open(f).convert('RGB')
        im = Image.new("RGB", (450, 170), "white")
        graphic.thumbnail((1000, 150), Image.ANTIALIAS)
        im.paste(graphic, (5, 5))
        draw = ImageDraw.Draw(im)
        for i, line in enumerate("".join(self.obscured).split(" ")):
            draw.text((120, 5 + i * 40), line.upper(), (0, 0, 0), font=guess_font)
        draw.text((120, 130), "Guessed: {}".format("".join(self.guessed)), (100, 100, 100), font=guessed_font)
        return im

    async def create_image_async(self):
        return await asyncio.get_event_loop().run_in_executor(None, self.create_image)


@commands.create("hangman", "hang", "h", category="Games", params=[Word("action")])
@channel_only
@games_allowed_only
async def hangman(message, action):
    """
    Play a game of hangman.

    Start a game with::

        hang start

    Then guess words::

        hang g

    """
    key = (message.transport.id, message.server.id, message.channel.id)
    if action == "start":
        if key in cache:
            game = cache[key]
        else:
            game = Game(random.choice(word_list))
            cache[key] = game

        return Response("", attachments=[ImageAttachment(await game.create_image_async(), "hangman.png")])
    elif re.match("^[A-Za-z]{1}$", action):
        try:
            game = cache[key]
        except KeyError:
            raise CommandError("Say 'start' to start a game first.")
        game.guess(action)

        if game.won:
            del cache[key]
            return Response("\N{TROPHY} \N{TROPHY} WINNER WINNER CHICKEN DINNER!! \N{TROPHY} \N{TROPHY}", attachments=[
                ImageAttachment(await game.create_image_async(), "hangman.png")
            ])
        elif game.lost:
            del cache[key]
            return Response("You all LOST! \N{LARGE RED CIRCLE}", attachments=[
                ImageAttachment(await game.create_image_async(), "hangman.png")
            ])
        else:
            return Response("", attachments=[ImageAttachment(await game.create_image_async(), "hangman.png")])
    else:
        raise CommandError("Either say 'start' or supply one letter to guess.")


def setup():
    commands.add(hangman)
