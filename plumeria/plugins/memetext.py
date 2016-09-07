import os.path
import re
import statistics

import pkg_resources
from PIL import ImageDraw
from PIL import ImageFont

from plumeria.command import commands
from plumeria.util.command import image_filter

IMPACT_FONT_PATH = os.path.join("fonts", "impact.ttf")


def draw_textbox(im, left_x, top_y, box_width, text, font, border_size=2, v_align='top'):
    draw = ImageDraw.Draw(im)
    words = re.split(" ", text)
    buffer = []
    lines = []
    widths = []
    heights = []
    last_fit_width = 0
    i = 0
    while i < len(words):
        word = words[i]
        line = " ".join(buffer + [word])
        w, h = draw.textsize(line, font=font)
        heights.append(h)
        if w <= box_width or not len(buffer):
            buffer.append(word)
            last_fit_width = w
            i += 1
        else:
            lines.append(" ".join(buffer))
            widths.append(last_fit_width)
            buffer = []
            last_fit_width = 0

    if len(buffer):
        lines.append(" ".join(buffer))
        widths.append(last_fit_width)

    h = statistics.mean(heights)

    if v_align == 'bottom':
        top_y -= h * len(lines)

    for x in range(-border_size, border_size + 1):
        for y in range(-border_size, border_size + 1):
            for i, line in enumerate(lines):
                line_x_offset = (box_width - widths[i]) // 2
                draw.text((left_x + line_x_offset + x, top_y + y + i * h), line, font=font, fill='black')

    for i, line in enumerate(lines):
        line_x_offset = (box_width - widths[i]) // 2
        draw.text((left_x + line_x_offset, top_y + i * h), line, font=font, fill='white')


def render_meme_text(im, text, v_align):
    text = text[:400] # limit text length
    w, h = im.size
    font_size = max(15, min(int(h * 0.9e-1), 200))

    if os.path.exists(IMPACT_FONT_PATH):
        with open(IMPACT_FONT_PATH, "rb") as f:
            font = ImageFont.truetype(f, font_size)
    else:
        with pkg_resources.resource_stream("plumeria", 'fonts/FiraSans-Regular.ttf') as f:
            font = ImageFont.truetype(f, font_size)

    draw_textbox(im, 20, 20 if v_align == 'top' else h - 40, w - 40, text, font,
                 border_size=max(1, min(int(w * h * 1e-5 * 2), 9)), v_align=v_align)


@commands.register('memetext', 'mt', category='Image')
@image_filter
def memetext(message, im):
    """
    Renders meme text at the top of the image.

    Example::

        /image awkward penguin template | mt Tried to use another bot

    Requires an input image.
    """
    render_meme_text(im, message.content, 'top')
    return im


@commands.register('memetext2', 'mb', category='Image')
@image_filter
def memetext2(message, im):
    """
    Renders meme text at the bottom of the image.

    Example::

        /lastimage | mb Rejected

    Requires an input image.
    """
    render_meme_text(im, message.content, 'bottom')
    return im
