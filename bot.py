#!/usr/bin/env python3
import asyncio
import pkgutil
import sys
import argparse
import logging
from plumeria import config
from plumeria.event import bus
import plumeria.plugins

logger = logging.getLogger(__name__)


async def startup():
    await bus.post('preinit')
    await bus.post('init')


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s [%(name)s] %(message)s")

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="config.ini")
    args = parser.parse_args()

    config.file = args.config

    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)

    loop = asyncio.get_event_loop()

    for importer, modname, ispkg in pkgutil.iter_modules(
            plumeria.plugins.__path__):
        logging.info("Loading plumeria.plugins.{}...".format(modname))
        __import__("plumeria.plugins." + modname)

    config.load()
    config.save()

    loop.run_until_complete(startup())
    loop.run_forever()
