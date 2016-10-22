"""Start a web server that plugins can add pages to."""

import asyncio
import os.path
import sys
from functools import wraps

from aiohttp import web
from docutils.core import publish_parts
from jinja2 import Environment, PackageLoader

from plumeria import config
from plumeria.event import bus

webserver_host = config.create("webserver", "host",
                               fallback="localhost",
                               comment="The hostname for the web server to bind to. Use 0.0.0.0 "
                                       "to bind to all interfaces or 127.0.0.1 to only access "
                                       "from localhost.")

webserver_port = config.create("webserver", "port", type=int,
                               fallback=8110,
                               comment="Web server port to serve on.")

public_address = config.create("webserver", "public_address",
                               fallback="",
                               comment="The public address used to access the internal web server. "
                                       "If not set, the address is detected automatically.")


class Route:
    def __init__(self, path, methods):
        self.path = path
        self.methods = methods


class Application:
    def __init__(self):
        self.app = web.Application()
        static_dir = os.path.join(os.path.dirname(sys.modules[__name__].__file__), '..', 'static')  # does not work with eggs
        self.app.router.add_static('/static/', static_dir, name='static')
        self.host = "127.0.0.1"
        self.port = 80

    async def get_base_url(self):
        address = public_address()
        if len(address):
            return "http://{}".format(address)
        else:
            return "http://{}:{}".format(self.host, self.port)

    async def run(self, host="127.0.0.1", port=8080):
        self.host = host
        self.port = port
        loop = asyncio.get_event_loop()
        await loop.create_server(self.app.make_handler(), host, port)

    def route(self, path, methods=None):
        if not methods: methods = ['GET']

        def decorator(f):
            f.webserver_route = Route(path, methods)
            return f

        return decorator

    def add(self, f):
        route = f.webserver_route

        @wraps(f)
        async def wrapper(*args, **kwargs):
            ret = await f(*args, **kwargs)
            if isinstance(ret, str):
                return web.Response(headers={"Content-Type": "text/html"}, body=ret.encode('utf-8'))
            else:
                return ret

        for method in route.methods:
            self.app.router.add_route(method, route.path, wrapper)

        return f


env = Environment(loader=PackageLoader('plumeria', 'templates'),
                  autoescape=True,
                  extensions=['jinja2.ext.autoescape'])

env.filters['rst2html'] = lambda s: publish_parts(s, writer_name='html')['html_body']


app = Application()


def render_template(name, **params):
    return env.get_template(name).render(params)


def setup():
    config.add(webserver_host)
    config.add(webserver_port)
    config.add(public_address)

    @bus.event("init")
    async def init():
        await app.run(host=webserver_host(), port=webserver_port())
