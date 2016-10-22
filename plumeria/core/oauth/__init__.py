"""Add support for OAuth to let users to connect the bot various services."""

from plumeria.command import commands
from plumeria.core.storage import pool, migrations
from plumeria.core.webserver import app, render_template
from plumeria.event import bus
from plumeria.message import Message, Response
from plumeria.perms import direct_only
from .manager import *
from .storage import *

__requires__ = ['plumeria.core.storage']


def find_endpoint(name) -> Endpoint:
    try:
        return oauth_manager.get_endpoint(name)
    except KeyError:
        raise CommandError("No such service **{}** exists.".format(name))


@commands.create('connect', cost=4, category='Services')
@direct_only
async def connect(message: Message):
    """
    Authenticate yourself to a service and provide the bot with permissions of your choosing.

    Example::

        /connect spotify
    """
    endpoint = find_endpoint(message.content.strip())

    try:
        url = await endpoint.request_authorization(message.author)
        return Response("You will have to visit this link to connect your account: {}" \
                        "\n\nYou can later disable access from your account settings on the website.".format(url),
                        private=True)
    except NotImplementedError as e:
        raise CommandError("Could not connect service: {}".format(str(e)))


@app.route("/oauth2/callback/", methods=['GET'])
async def handle(request):
    error = request.GET.get("error", "")
    code = request.GET.get("code", "")
    state = request.GET.get("state", "")
    if not len(error):
        try:
            await oauth_manager.process_request_authorization(state, code)
            return render_template("oauth/success.html")
        except UnknownFlowError:
            return render_template("oauth/error.html",
                                   error="The link you have visited has expired.")
        except FlowError:
            return render_template("oauth/error.html",
                                   error="We were unable to contact the service to check that you authorized access.")
    else:
        await oauth_manager.cancel_request_authorization(state, error)
        return render_template("oauth/error.html",
                               error="Something went wrong while connecting to the service. The service says: {}".format(
                                   error[:200]))


async def setup():
    commands.add(connect)
    app.add(handle)

    store = DatabaseTokens(pool, migrations)
    await store.initialize()
    oauth_manager.redirect_uri = await app.get_base_url() + "/oauth2/callback/"
    oauth_manager.store = store
