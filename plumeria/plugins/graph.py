import asyncio
import io
import re
import threading

import matplotlib
import numpy as np
import pkg_resources
from PIL import Image
from PIL import ImageChops

from plumeria.command import commands, CommandError
from plumeria.message import Response, MemoryAttachment, ImageAttachment
from plumeria.message.lists import parse_list, parse_numeric_list
from plumeria.util.ratelimit import rate_limit

matplotlib.use('Agg')

from matplotlib import rc
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

PERCENTAGE_PATTERN = re.compile("\\b([0-9]+\\.?[0-9]*)%?\\b")
NUMBER_PATTERN = re.compile("\\b([0-9]+\\.?[0-9]*)\\b")

rc('text', usetex=False)
font_path = pkg_resources.resource_filename("plumeria", 'fonts/FiraSans-Regular.ttf')
lock = threading.RLock()


def trim_whitespace(im):
    bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)


def extract_data(message, pattern, normalize=False):
    title = None
    labels = []
    data = []
    total_pct = 0

    for part in parse_list(message):
        m = pattern.search(part)
        if m:
            labels.append(pattern.sub("", part, 1).strip())
            pct = float(m.group(1)) / 100 if normalize else float(m.group(1))
            data.append(pct)
            total_pct += pct
        else:
            title = part.strip()

    if normalize:
        data = list(map(lambda x: x / total_pct, data))
    return title, labels, data


@commands.register("pie", category="Graphing")
@rate_limit()
async def pie(message):
    """
    Generate a pie graph. To specify the parts of the pie, make a
    list separated by new lines, semi-colons or commas where each
    list entry has a percentage in it (if there is more than one, the
    first percentage is used).

    To specify a graph title, don't provide a percentage for one of the
    list items.

    Example::

        /pie Materials, 40% Glass, 22%

    The percentages do not need to add up to 100%. If they do not, then
    the percentage values will be normalized so that they do add up to 100%.

    """
    title, labels, data = extract_data(message.content, pattern=PERCENTAGE_PATTERN, normalize=True)

    def execute():
        with lock:
            plt.figure(1, figsize=(5, 5))
            ax = plt.axes([0.1, 0.1, 0.4, 0.4])

            plt.pie(data, labels=labels, autopct='%1.0f%%', startangle=90)

            if title:
                plt.title(title)

            prop = fm.FontProperties(fname=font_path, size=11)
            for text in ax.texts:
                text.set_fontproperties(prop)

            buf = io.BytesIO()
            plt.savefig(buf, bbox_inches='tight', transparent=False, pad_inches=0.1)

            plt.clf()
        return buf

    buf = await asyncio.get_event_loop().run_in_executor(None, execute)

    return Response("", attachments=[MemoryAttachment(buf, "graph.png", "image/png")])


@commands.register("bar", category="Graphing")
@rate_limit()
async def bar(message):
    """
    Generate a bar graph. To specify the individual bar labels and values, make a
    list separated by new lines, semi-colons or commas where each
    list entry has a number in it (if there is more than one, the
    first number is used).

    To specify a graph title, don't provide a number for one of the
    list items.

    Example::

        /bar Groups, Man O 100, rationale. 20

    """
    title, labels, data = extract_data(message.content, pattern=NUMBER_PATTERN)

    def execute():
        width = 0.8
        ind = np.arange(len(data)) - width

        with lock:
            plt.figure(1, figsize=(5, 5))
            ax = plt.axes([0.1, 0.1, 0.4, 0.4])

            plt.bar(ind, data, width, align='center')
            plt.xticks(rotation=70)
            ax.set_xticks(ind)
            ax.set_xticklabels(labels)

            if title:
                plt.title(title)

            prop = fm.FontProperties(fname=font_path, size=11)
            for text in ax.texts:
                text.set_fontproperties(prop)

            buf = io.BytesIO()
            plt.savefig(buf, bbox_inches='tight', transparent=False, pad_inches=0.1)

            plt.clf()
        return buf

    buf = await asyncio.get_event_loop().run_in_executor(None, execute)

    return Response("", attachments=[MemoryAttachment(buf, "graph.png", "image/png")])


@commands.register("histogram", "hist", category="Graphing")
@rate_limit()
async def histogram(message):
    """
    Generate a histogram from a list of numbers separated by new lines, semi-colons,
    commas, or spaces. Currently, the bin count is locked to 10.

    Example::

        /hist 20 39 19 17 28 39 29 20 11 29 32 44
        /roll 500d10 | hist

    """
    data = parse_numeric_list(message.content)

    def execute():
        with lock:
            plt.figure(1, figsize=(5, 5))
            ax = plt.axes([0.1, 0.1, 0.4, 0.4])

            plt.hist(data, bins=10)

            prop = fm.FontProperties(fname=font_path, size=11)
            for text in ax.texts:
                text.set_fontproperties(prop)

            buf = io.BytesIO()
            plt.savefig(buf, bbox_inches='tight', transparent=False, pad_inches=0.1)

            plt.clf()
        return buf

    buf = await asyncio.get_event_loop().run_in_executor(None, execute)

    return Response("", attachments=[MemoryAttachment(buf, "graph.png", "image/png")])


@commands.register("tex", "latex", category="Image")
@rate_limit()
async def latex(message):
    """
    Renders LaTeX/TeX. Uses matplotlib to render instead of LaTeX.

    Example::

        /tex \\frac{-b\\pm\\sqrt{b^2-4ac}}{2a}

    """

    def execute():
        with lock:
            plt.figure(1, figsize=(1, 1))
            plt.axis("off")
            plt.title("${}$".format(message.content.replace("$", "\\$")))
            buf = io.BytesIO()
            try:
                plt.savefig(buf, bbox_inches='tight', transparent=False, pad_inches=0)
            except ValueError as e:
                raise CommandError("Render error: {}".format(str(e)))
            plt.clf()
            im = Image.open(buf)
            im = trim_whitespace(im)
            return im

    im = await asyncio.get_event_loop().run_in_executor(None, execute)

    return Response("", attachments=[ImageAttachment(im, "text.png")])
