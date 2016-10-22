"""Adds a help webpage and query functions for commands."""

import collections

import io

from plumeria.command import commands
from plumeria.message import Response, MemoryAttachment
from plumeria.core.webserver import app, render_template


@commands.create('help', 'commands', category='Utility')
async def help(message):
    """
    Get a listing of commands.
    """
    if not message.channel.is_private:
        server = message.channel.server.id
    else:
        server = "private"
    return Response(await app.get_base_url() + "/help/{}".format(server))


@commands.create('commands dump', category='Utility')
async def dump_commands(message):
    """
    Get a listing of commands in Markdown as a text file.
    """
    server = message.channel.server.id
    categories = set()
    by_category = collections.defaultdict(lambda: [])
    mappings = sorted(await commands.get_mappings(server), key=lambda m: m.command.category or "")
    for mapping in mappings:
        categories.add(mapping.command.category)
        by_category[mapping.command.category].append(mapping)
    categories = sorted(categories)
    buf = io.StringIO()
    for category in categories:
        buf.write("\n\n**{}**\n".format(category))
        for mapping in by_category[category]:
            buf.write("\n* {}".format(mapping.aliases[0]))
    return Response("See attachment", attachments=[
        MemoryAttachment(io.BytesIO(buf.getvalue().strip().encode("utf-8")), "commands.txt", "text/plain")
    ])


@app.route('/help/{server}')
async def handle(request):
    server_id = request.match_info['server']
    if server_id == "private":
        server_id = None
    categories = set()
    by_category = collections.defaultdict(lambda: [])
    mappings = sorted(await commands.get_mappings(server_id), key=lambda m: m.command.category or "")
    for mapping in mappings:
        categories.add(mapping.command.category)
        by_category[mapping.command.category].append(mapping)
    categories = sorted(categories)
    return render_template("help.html", commands=mappings, by_category=by_category, categories=categories)


def setup():
    commands.add(help)
    commands.add(dump_commands)
    app.add(handle)
