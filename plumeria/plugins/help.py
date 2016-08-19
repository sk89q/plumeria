import collections

from plumeria.command import commands
from plumeria.message import Response
from plumeria.webserver import app, render_template


@commands.register('help', 'commands', category='Utility')
async def help(message):
    """
    Get a listing of commands.
    """
    if hasattr(message.channel, "server"):
        server = message.channel.server.id
    else:
        server = "private"
    return Response(await app.get_base_url() + "/help/{}".format(server))


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
