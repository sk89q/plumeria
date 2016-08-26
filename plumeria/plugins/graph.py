import asyncio
import io
import re
import threading

import matplotlib
import pkg_resources

from plumeria.command import commands, CommandError
from plumeria.message import Response, MemoryAttachment
from plumeria.util.ratelimit import rate_limit

matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

PERCENTAGE_PATTERN = re.compile("([0-9]+\\.?[0-9]*)%")

font_path = pkg_resources.resource_filename("plumeria", 'fonts/FiraSans-Regular.ttf')
lock = threading.RLock()


def generate_pie(labels, data, title=None):
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


@commands.register("pie", category="Graphing")
@rate_limit()
async def image(message):
    """
    Generate a pie graph.

    """
    title = None
    labels = []
    data = []
    total_pct = 0

    if ';' in message.content:
        delimeter = ';'
    elif ',' in message.content:
        delimeter = ','
    else:
        raise CommandError("Split pie sections with ; or ,")

    for part in message.content.strip().split(delimeter):
        m = PERCENTAGE_PATTERN.search(part)
        if m:
            labels.append(PERCENTAGE_PATTERN.sub("", part, 1).strip())
            pct = float(m.group(1)) / 100
            data.append(pct)
            total_pct += pct
        else:
            title = part.strip()

    data = list(map(lambda x: x / total_pct, data))

    def execute():
        return generate_pie(labels, data, title=title)

    buf = await asyncio.get_event_loop().run_in_executor(None, execute)

    return Response("", attachments=[MemoryAttachment(buf, "graph.png", "image/png")])
