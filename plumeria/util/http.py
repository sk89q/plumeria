import json

import aiohttp
from aiohttp import TCPConnector
from aiohttp.errors import ClientConnectionError

from .network import NameResolver


class SelectiveConnector(TCPConnector):
    def __init__(self, *args, port_validator=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.port_validator = port_validator or (lambda p: p == 80 or p == 443)

    def connect(self, req):
        if not self.port_validator(req.port):
            raise ClientConnectionError("port {} is not permitted".format(req.port))
        return super().connect(req)


class DefaultClientSession(aiohttp.ClientSession):
    def __init__(self, *args, headers=None, connector=None, port_validator=None, **kwargs):
        if not headers: headers = {}
        headers['User-Agent'] = 'Discord chat bot'
        if not connector:
            connector = SelectiveConnector(resolver=NameResolver(),
                                           port_validator=port_validator)
        super().__init__(*args, headers=headers, connector=connector, **kwargs)


class BadStatusCodeError(Exception):
    def __init__(self, http_code, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.http_code = http_code


class Response:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self._text = text

    def text(self):
        return self._text

    def json(self):
        return json.loads(self._text)


async def request(*args, require_success=True, **kwargs):
    if 'data' in kwargs:
        if isinstance(kwargs['data'], dict) or isinstance(kwargs['data'], list):
            kwargs['data'] = json.dumps(kwargs['data'])
    with DefaultClientSession() as session:
        async with session.request(*args, **kwargs) as resp:
            if require_success and resp.status != 200:
                raise BadStatusCodeError(resp.status, "HTTP code is not 200; got {}\n\nCONTENT: {}".format(resp.status, await resp.text()))
            return Response(resp.status, await resp.text())


async def get(*args, **kwargs):
    return await request("get", *args, **kwargs)


async def post(*args, **kwargs):
    return await request("post", *args, **kwargs)


async def head(*args, **kwargs):
    return await request("head", *args, **kwargs)


class BaseRestClient:
    def __init__(self, session_cls=None, default_params=None):
        self.session_cls = session_cls or DefaultClientSession

    def preprocess(self, json):
        return json

    async def request(self, *args, **kwargs):
        with self.session_cls() as session:
            async with session.request(*args, **kwargs) as resp:
                if resp.status != 200:
                    raise APIError("HTTP code is not 200; got {}".format(resp.status))
                return self.preprocess(await resp.json())


class APIError(Exception):
    pass
