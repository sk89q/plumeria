"""Start a web server that plugins can add pages to."""

from plumeria import config
from plumeria.event import bus
from plumeria.webserver import app, public_address

webserver_host = config.create("webserver", "host",
                               fallback="localhost",
                               comment="The hostname for the web server to bind to. Use 0.0.0.0 "
                                       "to bind to all interfaces or 127.0.0.1 to only access "
                                       "from localhost.")

webserver_port = config.create("webserver", "port", type=int,
                               fallback=8110,
                               comment="Web server port to serve on.")


def setup():
    config.add(webserver_host)
    config.add(webserver_port)
    config.add(public_address)

    @bus.event("init")
    async def init():
        await app.run(host=webserver_host(), port=webserver_port())
