import functools
import random
import re
import string
from enum import Enum

import PIL
import asyncio
import cachetools
import pkg_resources
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from plumeria import config
from plumeria.command import CommandError, commands, channel_only
from plumeria.command.parse import Word
from plumeria.config import percent
from plumeria.config.common import games_allowed_only
from plumeria.core.scoped_config import scoped_config
from plumeria.message import ImageAttachment, Response
from plumeria.message.lists import parse_list
from plumeria.perms import owners_only

bomb_chance = config.create("minesweeper", "bomb_chance", type=percent, fallback=20, scoped=True, private=False,
                            comment="The % of a cell being a bomb")

POS_RE = re.compile("^([A-Za-z]+)([0-9]+)$")


def cell_name(x, y):
    return string.ascii_uppercase[x] + str(y + 1)


def draw_centered_text(draw, x, y, text, *args, font, **kwargs):
    w, h = draw.textsize(text, font=font)
    draw.text((x - w / 2, y - h / 2), text, *args, font=font, **kwargs)


def load_tile_graphics():
    images = {}
    for play in Play:
        with pkg_resources.resource_stream(__name__, "assets/{}.png".format(play.name.lower())) as f:
            images[play] = Image.open(f).convert('RGBA')
    return images


class Play(Enum):
    UNKNOWN = 'unknown'
    CLEAR = 'clear'
    FLAGGED = 'flagged'
    EXPLODED = 'exploded'


class State(Enum):
    IN_PLAY = 'in_play'
    WON = 'won'
    LOST = 'lost'


UNKNOWN_OR_FLAGGED = {Play.UNKNOWN, Play.FLAGGED}
TILE_GRAPHICS = load_tile_graphics()


class Game:
    def __init__(self, w, h, mine_fraction, r=None):
        r = random or random.Random()
        self.width = w
        self.height = h
        self.bomb_map = list(map(lambda y: list(map(lambda x: r.random() <= mine_fraction, range(w))), range(h)))
        self.play = list(map(lambda y: list(map(lambda x: Play.UNKNOWN, range(w))), range(h)))
        self.state = State.IN_PLAY
        self.remaining_unknown = w * h
        self.bomb_count = 0

        self.cell_size = 25

        with pkg_resources.resource_stream("plumeria", 'fonts/FiraSans-Regular.ttf') as f:
            self.cell_font = ImageFont.truetype(f, 10)
        with pkg_resources.resource_stream("plumeria", 'fonts/FiraSans-Regular.ttf') as f:
            self.count_font = ImageFont.truetype(f, 15)

        # count bombs
        for x in range(w):
            for y in range(h):
                if self.bomb_map[x][y]:
                    self.bomb_count += 1
                    self.remaining_unknown -= 1

        if self.bomb_count == 0:
            raise CommandError("No bombs found in created game! Make sure the bomb "
                               "`minesweeper/bomb_chance` setting is not near 0%.")

        # start it off
        tries = 0
        while self.remaining_unknown > 0 and tries < 20:
            x = r.randrange(0, self.width)
            y = r.randrange(0, self.height)
            if not self.bomb_map[x][y] and not self._count_adjacent_bombs(x, y):
                self.click(x, y)
                break
            tries += 1

    def create_image(self, cheat=False) -> PIL.Image.Image:
        w = self.width * self.cell_size
        h = self.height * self.cell_size
        im = Image.new("RGBA", (w, h), "white")
        draw = ImageDraw.Draw(im)
        for y in range(self.height):
            for x in range(self.width):
                cx = (x + 0.5) * self.cell_size
                cy = (y + 0.5) * self.cell_size
                play = self.play[x][y]

                # draw background
                tile = TILE_GRAPHICS[play].copy().resize((self.cell_size, self.cell_size), PIL.Image.BICUBIC)
                im.paste(tile, (x * self.cell_size, y * self.cell_size), mask=tile)

                # location text
                if play in UNKNOWN_OR_FLAGGED:
                    draw.text((x * self.cell_size + 2, y * self.cell_size + 2), cell_name(x, y), (68, 68, 150),
                              font=self.cell_font)

                if play == Play.CLEAR:
                    count = self._count_adjacent_bombs(x, y)
                    if count:
                        draw_centered_text(draw, cx, cy - 2, str(count), (217, 50, 50), font=self.count_font)

                if cheat and self.bomb_map[x][y]:
                    draw_centered_text(draw, cx, cy - 2, "XX", (217, 50, 50), font=self.count_font)

        return im

    async def create_image_async(self, *args, **kwargs):
        return await asyncio.get_event_loop().run_in_executor(None,
                                                              functools.partial(self.create_image, *args, **kwargs))

    def parse_pos(self, str):
        m = POS_RE.match(str)
        if not m:
            raise CommandError("Invalid position '{}' (expected something like C2)".format(str))
        x = string.ascii_uppercase.find(m.group(1).upper())
        y = int(m.group(2)) - 1
        if self._in_bounds(x, y):
            return x, y
        else:
            raise CommandError("Your position '{}' isn't in the grid!".format(str))

    def toggle_flag(self, x, y):
        if self.state != State.IN_PLAY:
            raise AssertionError("invalid state")
        if self.play[x][y] in (Play.UNKNOWN, Play.FLAGGED):
            self.play[x][y] = Play.FLAGGED if self.play[x][y] == Play.UNKNOWN else Play.UNKNOWN
        else:
            raise CommandError("You can't flag that cell!")

    def click(self, x, y):
        if self.state != State.IN_PLAY:
            raise AssertionError("invalid state")
        if self.play[x][y] in (Play.UNKNOWN, Play.FLAGGED):
            if self.bomb_map[x][y]:  # bomb
                self._mutate_cell(x, y, Play.EXPLODED)
                self.state = State.LOST
            else:
                self._clear_cell(x, y, set())
            if self.remaining_unknown == 0:
                self.state = State.WON
        else:
            raise CommandError("You can't flag that cell!")

    def _in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def _is_bomb(self, x, y):
        return self._in_bounds(x, y) and self.bomb_map[x][y]

    def _count_adjacent_bombs(self, x, y):
        return sum([
            self._is_bomb(x - 1, y),
            self._is_bomb(x, y - 1),
            self._is_bomb(x + 1, y),
            self._is_bomb(x, y + 1),
            self._is_bomb(x - 1, y - 1),
            self._is_bomb(x - 1, y + 1),
            self._is_bomb(x + 1, y - 1),
            self._is_bomb(x + 1, y + 1),
        ])

    def _clear_cell(self, x, y, visited):
        if not self._in_bounds(x, y):
            return
        if (x, y) in visited:
            return
        visited.add((x, y))
        if self.play[x][y] in UNKNOWN_OR_FLAGGED and not self.bomb_map[x][y]:
            self._mutate_cell(x, y, Play.CLEAR)
            if not self._count_adjacent_bombs(x, y):
                self._clear_cell(x - 1, y, visited)
                self._clear_cell(x, y - 1, visited)
                self._clear_cell(x + 1, y, visited)
                self._clear_cell(x, y + 1, visited)
                self._clear_cell(x - 1, y - 1, visited)
                self._clear_cell(x - 1, y + 1, visited)
                self._clear_cell(x + 1, y - 1, visited)
                self._clear_cell(x + 1, y + 1, visited)

    def _mutate_cell(self, x, y, new_play: Play):
        if self.play[x][y] in UNKNOWN_OR_FLAGGED and new_play != Play.UNKNOWN:
            self.remaining_unknown -= 1
            self.play[x][y] = new_play
        else:
            raise AssertionError("this shouldn't happen (is {}, wants to be {})".format(self.play[x][y], new_play))


cache = cachetools.LRUCache(maxsize=1000)


@commands.create("minesweeper start", "mine start", "m start", category="Games", params=[])
@channel_only
@games_allowed_only
async def start(message):
    """
    Starts a game of minesweeper.

    Example::

        mine start

    """
    key = (message.transport.id, message.server.id, message.channel.id)

    if key in cache:
        game = cache[key]
    else:
        game = Game(12, 12, scoped_config.get(bomb_chance, message.channel) / 100, random.Random())
        cache[key] = game

    return Response("", attachments=[ImageAttachment(await game.create_image_async(), "minesweeper.png")])


@commands.create("minesweeper", "mine", "m", category="Games")
@channel_only
@games_allowed_only
async def click(message):
    """
    Click one or more cells on minesweeper.

    Start a game with::

         mine start

    Then choose one or more cells::

        mine b5 e-g7 a7 a1-3

    """
    key = (message.transport.id, message.server.id, message.channel.id)

    try:
        game = cache[key]  # type: Game
    except KeyError:
        raise CommandError("Say 'start' to start a game first.")

    positions = parse_list(message.content)
    for position in positions:
        game.click(*game.parse_pos(position))

    if game.state == State.WON:
        del cache[key]
        return Response("\N{TROPHY} \N{TROPHY} YOU ARE WINNER! \N{TROPHY} \N{TROPHY}", attachments=[
            ImageAttachment(await game.create_image_async(), "minesweeper.png")
        ])
    elif game.state == State.LOST:
        del cache[key]
        return Response("\N{BOMB} \N{COLLISION SYMBOL} \N{COLLISION SYMBOL} BOOOOM!!!", attachments=[
            ImageAttachment(await game.create_image_async(), "minesweeper.png")
        ])
    else:
        return Response("", attachments=[ImageAttachment(await game.create_image_async(), "minesweeper.png")])


@commands.create("minesweeper flag", "mine flag", "m flag", category="Games")
@channel_only
@games_allowed_only
async def flag(message):
    """
    Toggle a flag on a cell on minesweeper.

    """
    key = (message.transport.id, message.server.id, message.channel.id)

    try:
        game = cache[key]  # type: Game
    except KeyError:
        raise CommandError("Say 'start' to start a game first.")

    positions = parse_list(message.content)
    for position in positions:
        game.toggle_flag(*game.parse_pos(position))
    return Response("", attachments=[ImageAttachment(await game.create_image_async(), "minesweeper.png")])


@commands.create("minesweeper cheat", "mine cheat", category="Games", params=[])
@channel_only
@owners_only
async def cheat(message):
    """
    Bot administrator command to show where bombs are for testing.

    """
    key = (message.transport.id, message.server.id, message.channel.id)

    try:
        game = cache[key]  # type: Game
    except KeyError:
        raise CommandError("Say 'start' to start a game first.")

    return Response("", attachments=[ImageAttachment(await game.create_image_async(cheat=True), "minesweeper.png")])


def setup():
    config.add(bomb_chance)
    commands.add(start)
    commands.add(click)
    commands.add(flag)
    commands.add(cheat)
