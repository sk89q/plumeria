#!/usr/bin/env python3
import argparse
import asyncio
import logging
import os.path
import sys

import plumeria.core
from plumeria import config
from plumeria.event import bus
from plumeria.plugin import PluginFinder, PluginLoader

logger = logging.getLogger(__name__)


async def startup():
    logging.info("Calling all setup handlers...")
    await bus.post('setup')
    logging.info("Calling all pre-init handlers...")
    await bus.post('preinit')
    logging.info("Starting...")
    await bus.post('init')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action='store_true', default=False)
    parser.add_argument("--config", type=str, default="config.ini")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s [%(name)s] %(message)s")

    config.file = args.config

    loop = asyncio.get_event_loop()

    plugins_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "plugins"))
    sys.path.insert(0, plugins_dir)
    sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__))))

    config.load()  # load list of plugins from config
    finder = PluginFinder()
    finder.search_package("plumeria.core", plumeria.core.__path__)
    try:
        import orchard
        finder.search_package("orchard", orchard.__path__)
    except ImportError:
        pass
    finder.from_config(config)
    config.save()  # save list of plugins

    loader = PluginLoader(config)
    loader.load(finder.modules)
    config.load()  # write new settings to config
    config.save()  # save final config

    if len(loader.plugins):
        loop.run_until_complete(startup())
        loop.run_forever()
    else:
        logging.warning("No plugins are enabled! Exiting...")
        sys.exit(1)
