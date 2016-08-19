import asyncio
import sys
from docutils.core import publish_parts

import os.path
from aiohttp import web
from functools import wraps
from jinja2 import Environment, PackageLoader
from . import config

public_address = config.create("webserver", "public_address",
                               fallback="",
                               comment="The public address used to access the internal web server. "
                                       "If not set, the address is detected automatically.")

env = Environment(loader=PackageLoader('plumeria', 'templates'),
                  autoescape=True,
                  extensions=['jinja2.ext.autoescape'])

env.filters['rst2html'] = lambda s: publish_parts(s, writer_name='html')['html_body']


class Application:
    def __init__(self):
        self.app = web.Application()
        static_dir = os.path.join(os.path.dirname(sys.modules[__name__].__file__), 'static')  # does not work with eggs
        self.app.router.add_static('/static/', static_dir, name='static')

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
            @wraps(f)
            async def wrapper(*args, **kwargs):
                ret = await f(*args, **kwargs)
                if isinstance(ret, str):
                    return web.Response(headers={"Content-Type": "text/html"}, body=ret.encode('utf-8'))
                else:
                    return ret

            for method in methods:
                self.app.router.add_route(method, path, wrapper)
            return f

        return decorator


def render_template(name, **params):
    return env.get_template(name).render(params)


app = Application()
