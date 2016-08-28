import asyncio
import io
import os
import subprocess
import threading

import dot_parser
from dot_parser import graph_definition
from pyparsing import ParseException

from plumeria.command import commands, CommandError
from plumeria.message import Response, MemoryAttachment
from plumeria.util.message import strip_markdown_code
from plumeria.util.ratelimit import rate_limit

lock = threading.RLock()


def parse_dot_data(s):
    with lock:
        dot_parser.top_graphs = []  # Clear list of existing graphs because this module is bad
        parser = graph_definition()
        parser.parseWithTabs()
        tokens = parser.parseString(s)
        return list(tokens)


def render_dot(graph, format="png"):
    program = 'dot'
    if os.name == 'nt' and not program.endswith('.exe'):
        program += '.exe'

    p = subprocess.Popen(
        [program, '-T' + format],
        shell=False,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE)

    stdout, stderr = p.communicate(input=graph.to_string().encode('utf-8'))

    if p.returncode != 0:
        raise Exception("Received non-zero return code from grapviz\n\nError: {}".format(stderr.decode('utf-8')))

    return stdout


async def handle_request(message, type):
    content = strip_markdown_code(message.content.strip())

    def execute():
        # Use parser as a rudimentary validator
        graph = parse_dot_data(type + " G {\n" + content + "\n}")[0]
        buf = io.BytesIO()
        buf.write(render_dot(graph, format="png"))
        return buf

    try:
        buf = await asyncio.get_event_loop().run_in_executor(None, execute)
        return Response("", attachments=[MemoryAttachment(buf, "graph.png", "image/png")])
    except ParseException as e:
        raise CommandError("Parse error: {}".format(str(e)))


@commands.register("graph", category="Graphing")
@rate_limit()
async def graph(message):
    """
    Generates a non-directed graph using DOT syntax and drawn using Graphviz.

    Example::

        /graph
        a -- b
        b -- c
        c -- a

    """
    return await handle_request(message, "graph")


@commands.register("digraph", category="Graphing")
@rate_limit()
async def digraph(message):
    """
    Generates a directed graph using DOT syntax and drawn using Graphviz.

    Example::

        /digraph
        a -> b
        b -> c
        c -> a

    """
    return await handle_request(message, "digraph")
