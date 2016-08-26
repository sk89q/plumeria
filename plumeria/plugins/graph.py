import asyncio
import io
import re
import threading

import matplotlib
import numpy as np
import pkg_resources

from plumeria.command import commands, CommandError
from plumeria.message import Response, MemoryAttachment
from plumeria.util.message import split_array, split_numbers
from plumeria.util.ratelimit import rate_limit

matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

PERCENTAGE_PATTERN = re.compile("([0-9]+\\.?[0-9]*)%")
NUMBER_PATTERN = re.compile("([0-9]+\\.?[0-9]*)")

font_path = pkg_resources.resource_filename("plumeria", 'fonts/FiraSans-Regular.ttf')
lock = threading.RLock()


def extract_data(message, pattern, normalize=False):
    title = None
    labels = []
    data = []
    total_pct = 0

    for part in split_array(message):
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
    Generate a pie graph.

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
    Generate a pie graph.

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
    Generate a histogram.

    """
    data = split_numbers(message.content)

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
