"""Add support for OAuth to let users to connect the bot various services."""

from plumeria.command import CommandError, commands
from plumeria.event import bus
from plumeria.message import Message, Response
from plumeria.middleware.oauth import oauth_manager, Endpoint, UnknownFlowError, FlowError
from plumeria.perms import direct_only
from plumeria.webserver import app, render_template


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

def setup():
    @bus.event('preinit')
    async def preinit():
        oauth_manager.redirect_uri = await app.get_base_url() + "/oauth2/callback/"

    commands.add(connect)
    app.add(handle)
