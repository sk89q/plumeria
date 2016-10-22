"""Server to render HTML and webpages for the main webcap plugin."""

import asyncio
import io
import logging
import os
import random
import re
import string
from hmac import compare_digest
from json import JSONDecodeError

from PIL import Image
from PIL import ImageChops
from aiohttp.web import json_response, Response
from selenium import webdriver
from selenium.common.exceptions import TimeoutException

from plumeria import config
from plumeria.plugin import PluginSetupError
from plumeria.core.webserver import app

VALID_URL_REGEX = re.compile("^(?:https?://|data:)", re.IGNORECASE)

logger = logging.getLogger(__name__)


def generate_key(length):
    chars = string.ascii_letters + string.digits + '_-@.,'
    random.seed = os.urandom(1024)
    return ''.join(random.choice(chars) for i in range(length))


api_key = config.create("webcap_server", "key",
                        fallback=generate_key(48),
                        comment="The API that must be provided to use this webcap server")

page_load_timeout = config.create("webcap_server", "page_load_timeout",
                                  type=int,
                                  fallback=10,
                                  comment="Number of seconds before timing out page load")


def trim(im):
    bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)
    else:
        return im


@app.route('/webcap-server/render/', methods=['POST'])
async def handle(request):
    try:
        json = await request.json()
    except JSONDecodeError:
        return json_response(status=400, data={'error': 'invalid post body (expected valid JSON)'})

    test_key = json.get("key", "")
    if not compare_digest(test_key, api_key()):
        return json_response(status=401, data={'error': 'bad API key'})

    url = json.get("url", "")
    if not VALID_URL_REGEX.match(url):
        return json_response(status=400, data={'error': 'bad URL'})

    trim_image = json.get("trim", "false").lower() == "true"

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
        logger.info("Requesting {} via Selenium/PhantomJS...".format(url))

        try:
            driver = webdriver.PhantomJS(executable_path='node_modules/phantomjs/lib/phantom/bin/phantomjs')
            driver.set_window_size(width, 768)
            driver.set_page_load_timeout(page_load_timeout())
            driver.get(url)
            data = io.BytesIO()
            data.write(driver.get_screenshot_as_png())
        except TimeoutException:
            logger.warn("Request for {} timed out".format(url), exc_info=True)
            return json_response(status=400, data={'error': 'timeout'})
        except Exception:
            logger.warn("Request for {} encountered an error".format(url), exc_info=True)
            return json_response(status=500, data={'error': 'a rendering error occurred'})

        try:
            im = Image.open(data)
        except OSError:
            logger.warn("Request for {} resulted in an image file that could not be opened".format(url), exc_info=True)
            return json_response(status=500, data={'error': 'failed to read rendered image'})

        w, h = im.size
        im = im.crop((0, 0, min(w, width), min(h, max_height)))
        if trim_image:
            im = trim(im)
        buffer = io.BytesIO()
        im.save(buffer, "png")
        return Response(body=buffer.getvalue(), content_type="image/png")

    return await asyncio.get_event_loop().run_in_executor(None, execute)


def setup():
    config.add(api_key)
    config.add(page_load_timeout)

    if not api_key():
        raise PluginSetupError("This plugin requires an API key to be chosen.")

    app.add(handle)
