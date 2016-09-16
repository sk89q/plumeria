#!/usr/bin/env python3
import asyncio
import os.path
import pkgutil
import sys
import argparse
import logging
from plumeria import config
from plumeria.config import boolstr
from plumeria.event import bus
import plumeria.plugins

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

    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)

    loop = asyncio.get_event_loop()

    plugins_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "plugins"))
    logging.info("Added {} as an extra source for plugins".format(plugins_dir))
    sys.path.insert(0, plugins_dir)

    discovered_modules = list(pkgutil.iter_modules(plumeria.plugins.__path__))
    modules_to_load = set()

    # Discover list of modules to load and save it to config
    config.load()
    for importer, modname, ispkg in discovered_modules:
        path = "plumeria.plugins." + modname
        enabled = config.create("plugins", path, type=boolstr, fallback=False)
        if enabled():
            modules_to_load.add(path)
    config.save()

    # Add extra modules that are specified in the config file
    for path in config.reader['plugins'].keys():
        if boolstr(config.reader.get("plugins", path, fallback="")):
            modules_to_load.add(path)

    for path in modules_to_load:
        logging.info("Loading {}...".format(path))
        try:
            __import__(path)
        except:
            logging.warning("Failed to load {}".format(path), exc_info=True)

    config.load()
    config.save()

    if len(modules_to_load):
        loop.run_until_complete(startup())
        loop.run_forever()
    else:
        logging.warning("Please enable at least one plugin in the configuration file")

