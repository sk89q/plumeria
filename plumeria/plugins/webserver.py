from plumeria import config
from plumeria.event import bus
from plumeria.webserver import app

webserver_host = config.create("webserver", "host",
                               comment="The hostname for the web server to bind to. Use 0.0.0.0 "
                                       "to bind to all interfaces or 127.0.0.1 to only access "
                                       "from localhost.")

webserver_port = config.create("webserver", "port", type=int,
                               comment="Web server port to serve on.")


@bus.event("init")
async def init():
    await app.run(host=webserver_host(), port=webserver_port())
