import asyncio
import importlib
import inspect
import logging
import pkgutil
from enum import Enum

from plumeria import config
from plumeria.config import boolstr, ManagedConfig

logger = logging.getLogger(__name__)

enable_new = config.create("plugin_loader", "enable-new-plugins", type=boolstr, fallback="false",
                           comment="Set true to automatically enable new detected plugins")
config.add(enable_new)


class PluginSetupError(Exception):
    """Raised when a plugin can't be enabled."""


class PluginLoadError(Exception):
    """Raised when a plugin can't be loaded."""

    def __init__(self, path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = path


class PluginImportError(PluginLoadError):
    """Raised when a plugin can't be import."""


class PluginDisabledError(PluginLoadError):
    """Raised when a plugin cannot be loaded because it has not been enabled."""


class CircularDependencyError(PluginLoadError):
    """Raised when plugins require each other in a loop."""

    def __init__(self, path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = path


class PluginFinder:
    def __init__(self):
        self.modules = set()

    def from_config(self, config: ManagedConfig):
        """
        Get plugins to load from a configuration file.

        Parameters
        ----------
        config : :class:`ManagedConfig`
            The configuration
        -------

        """
        for path in config.reader['plugins'].keys():
            if boolstr(config.reader.get("plugins", path, fallback="")):
                self.modules.add(path)

    def search_package(self, package: str, path: str):
        """
        Find plugins within a package.

        Parameters
        ----------
        package : str
            The package to look in
        path : str
            The path to look in

        """
        discovered_modules = list(pkgutil.iter_modules(path))

        for importer, modname, ispkg in discovered_modules:
            path = package + "." + modname
            self.modules.add(path)


class State(Enum):
    PENDING = 'pending'
    LOADING = 'loading'
    LOADED = 'loaded'
    FAILED = 'failed'


class Plugin:
    def __init__(self, path):
        self.path = path
        self.state = State.PENDING


class PluginLoader:
    def __init__(self, config):
        self.config = config
        self.plugins = {}

    def load(self, paths):
        paths_to_load = []

        for path in paths:
            enabled_by_default = "True" if path.startswith("plumeria.core.") or enable_new() else "False"
            enabled = self.config.add(self.config.create("plugins", path, type=boolstr, fallback=enabled_by_default))
            if enabled():
                if path not in self.plugins:
                    self.plugins[path] = Plugin(path)
                    paths_to_load.append(path)

        for path in paths_to_load:
            try:
                self._load(path)
            except IndexError:
                break
            except (PluginLoadError, PluginSetupError):
                continue  # already logged

    def _load(self, path: str):
        try:
            plugin = self.plugins[path]
        except KeyError:
            raise PluginDisabledError(path)

        if plugin.state == State.FAILED:
            raise PluginLoadError(path)
        elif plugin.state == State.LOADING:
            raise CircularDependencyError(path)
        elif plugin.state == State.LOADED:
            return

        plugin.state = State.LOADING
        logger.info("Loading {}...".format(plugin.path))

        try:
            module = importlib.import_module(path)
        except Exception as e:
            plugin.state = State.FAILED
            logger.error("Failed to impory {}".format(path), exc_info=True)
            raise PluginImportError("failed to import") from e

        try:
            # load dependencies
            if hasattr(module, "__requires__"):
                for dep_path in module.__requires__:
                    self._load(dep_path)

            if hasattr(module, "setup"):
                if inspect.iscoroutinefunction(module.setup):
                    asyncio.get_event_loop().run_until_complete(module.setup())
                else:
                    module.setup()
            else:
                plugin.state = State.FAILED
                raise PluginSetupError("No setup() entry point exists for the plugin. If this is your plugin, make "
                                       "sure to add one. Plugins for older versions of Plumeria lack this and that "
                                       "may be why you are getting this message.")
            plugin.state = State.LOADED

        except PluginDisabledError as e:
            plugin.state = State.FAILED
            logger.error("Failed to load '{path}' because it needs the plugin '{dep}' to be enabled"
                         .format(path=plugin.path, dep=e.path), exc_info=False)
            raise PluginLoadError(path) from e

        except CircularDependencyError as e:
            plugin.state = State.FAILED
            logger.error("Failed to load '{}' because it has circular dependencies".format(plugin.path), exc_info=False)
            raise PluginLoadError(path) from e

        except PluginLoadError as e:
            plugin.state = State.FAILED
            logger.error(
                "Failed to load '{path}' because it depends on '{dep}' which failed to load"
                    .format(dep=e.path, path=plugin.path), exc_info=False)
            raise PluginLoadError(path) from e

        except PluginSetupError as e:
            plugin.state = State.FAILED
            logger.error("Failed to initialize '{}': {}".format(plugin.path, str(e)), exc_info=False)
            raise PluginLoadError(path) from e

        except Exception as e:
            plugin.state = State.FAILED
            logger.error("Failed to load '{}'".format(plugin.path), exc_info=True)
            raise PluginLoadError(path) from e
