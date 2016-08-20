import asyncio
import shlex
import textwrap
import pkg_resources

from PIL import Image, ImageFilter, ImageDraw, ImageFont
from plumeria.command import commands, ArgumentParser
from plumeria.message import Response, ImageAttachment
from plumeria.util.ratelimit import rate_limit
from plumeria.util.command import image_filter

MARGIN = 20
TEXT_WIDTH = 50
with pkg_resources.resource_stream("plumeria", 'fonts/FiraSans-Regular.ttf') as f:
    FONT = ImageFont.truetype(f, 22)


@commands.register('drawtext', category='Image')
@rate_limit(burst_size=2)
async def drawtext(message):
    """
    Generates an image with given text.
    """
    def execute():
        im = Image.new('RGB', (1, 1), (0, 0, 0, 0))
        draw = ImageDraw.Draw(im)

        lines = textwrap.wrap(message.content, width=TEXT_WIDTH)
        dimensions = []
        max_width = 0
        max_height = 0

        for line in lines:
            w, h = draw.textsize(line, font=FONT)
            dimensions.append((w, h))
            max_width = max(max_width, w)
            max_height = max(max_height, h)

        im = Image.new('RGB', (max_width + MARGIN * 2, max_height * len(lines) + MARGIN * 2), (0, 0, 0, 0))
        draw = ImageDraw.Draw(im)

        for i in range(0, len(lines)):
            line = lines[i]
            w, h = dimensions[i]
            draw.text(((max_width - w) / 2 + MARGIN, max_height * i + MARGIN), line, font=FONT)

        return im

    im = await asyncio.get_event_loop().run_in_executor(None, execute)
    return Response("", [ImageAttachment(im, "text.png")])


@commands.register('blur', category='Image')
@image_filter
def blur(message, im):
    """
    Applies a blur effect.

    Requires an input image.
    """
    parser = ArgumentParser()
    parser.add_argument("--radius", "-r", type=int, choices=range(2, 10), default=2)
    args = parser.parse_args(shlex.split(message.content))
    return im.filter(ImageFilter.GaussianBlur(radius=args.radius))


@commands.register('edgeenhance', category='Image')
@image_filter
def edgeenhance(message, im):
    """
    Applies an edge enhance effect.

    Requires an input image.
    """
    return im.filter(ImageFilter.EDGE_ENHANCE)


@commands.register('emboss', category='Image')
@image_filter
def emboss(message, im):
    """
    Applies a emboss effect.

    Requires an input image.
    """
    return im.filter(ImageFilter.EMBOSS)


@commands.register('findedges', category='Image')
@image_filter
def findedges(message, im):
    """
    Applies a find-edges effect.

    Requires an input image.
    """
    return im.filter(ImageFilter.FIND_EDGES)


@commands.register('sharpen', category='Image')
@image_filter
def sharpen(message, im):
    """
    Applies a sharpen effect.

    Requires an input image.
    """
    return im.filter(ImageFilter.SHARPEN)


@commands.register('bw', 'blackandwhite', 'blacknwhite', 'blackwhite', category='Image')
@image_filter
def bw(message, im):
    """
    Applies a black and white effect.

    Requires an input image.
    """
    return im.convert('1').convert("RGB")
