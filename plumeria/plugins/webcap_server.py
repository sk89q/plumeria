import asyncio
import io
import os
import random
import re
import string
from json import JSONDecodeError
from tempfile import NamedTemporaryFile

from PIL import Image
from aiohttp.web import json_response, Response
from selenium import webdriver

from plumeria import config
from plumeria.webserver import app

VALID_URL_REGEX = re.compile("^https?://", re.IGNORECASE)


def generate_key(length):
    chars = string.ascii_letters + string.digits + '_-@.,'
    random.seed = os.urandom(1024)
    return ''.join(random.choice(chars) for i in range(length))


api_key = config.create("webcap_server", "key",
                        fallback=generate_key(32),
                        comment="The API that must be provided to use this webcap server")


@app.route('/webcap-server/render/', methods=['POST'])
async def handle(request):
    try:
        json = await request.json()
    except JSONDecodeError:
        return json_response(status=400, data={'error': 'invalid post body (expected valid JSON)'})

    test_key = json.get("key", "")
    if test_key != api_key():
        return json_response(status=401, data={'error': 'bad API key'})

    url = json.get("url", "")
    if not VALID_URL_REGEX.match(url):
        return json_response(status=400, data={'error': 'bad URL'})

    try:
        width = int(json.get("width", "1024"))
        if width < 100 or width > 2048:
            raise ValueError("width out of bounds")
    except ValueError:
        return json_response(status=400, data={'error': 'width is not a valid number'})

    try:
        max_height = int(json.get("max_height", "1024"))
        if max_height < 100 or max_height > 4096:
            raise ValueError("max_height out of bounds")
    except ValueError:
        return json_response(status=400, data={'error': 'max_height is not a valid number'})

    def execute():
        driver = webdriver.PhantomJS(executable_path='node_modules/phantomjs/lib/phantom/bin/phantomjs')
        driver.set_window_size(width, 768)
        driver.get(url)
        with NamedTemporaryFile(delete=False) as file:
            driver.save_screenshot(file.name)
        im = Image.open(file.name)
        w, h = im.size
        im = im.crop((0, 0, min(w, width), min(h, max_height)))
        buffer = io.BytesIO()
        im.save(buffer, "jpeg", quality=80)
        return buffer.getvalue()

    buf = await asyncio.get_event_loop().run_in_executor(None, execute)
    return Response(body=buf, content_type="image/png")
