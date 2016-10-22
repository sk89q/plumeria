"""Implementation of per-server and per-channel configuration settings."""

import logging
from typing import Optional, Union, Sequence, Any

from plumeria.config import Setting
from plumeria.event import bus
from plumeria.transport import Channel
from plumeria.transport import Server
from plumeria.util.collections import tree, tree_get, tree_delete, gather_tree_nodes

logger = logging.getLogger(__name__)

NO_PROVIDER_ERROR = "A plugin that allows the bot to save these configuration values somewhere (like to a database) " \
                    "needs to be enabled."


class ScopedValue:
    """
    Holds a scoped configuration value.

    The non-scoped analogue to this class is :class:`plumeria.config.Value`.

    Attributes
    ----------
    transport : str
        The ID of the transport
    server : str
        The ID of the server
    channel : str
        The ID of the channel
    section : str
        The section
    key : str
        The key
    value : str
        The raw value

    """

    __slots__ = ('transport', 'server', 'channel', 'section', 'key', 'value')

    def __init__(self, transport: str, server: str, channel: Optional[str], section: str, key: str, value: str):
        self.transport = transport
        self.server = server
        self.channel = channel
        self.section = section
        self.key = key
        self.value = value


class ScopedConfigProvider:
    """
    A base class that must be extended and registered with :class:`ScopedConfig` so there's a way to
    actually store these scoped configuration values.

    """

    async def get_all(self, server: Server) -> Sequence[ScopedValue]:
        """
        Get all configuration values set for a server.

        Parameters
        ----------
        server : :class:`plumeria.transport.Server`
            An instance of a server

        Returns
        -------
        Sequence[:class:`ScopedValue`]
            A sequence of scoped values

        """
        raise NotImplementedError(NO_PROVIDER_ERROR)

    async def save(self, sv: ScopedValue):
        """
        Save the given configuration option to persistent store.

        Parameters
        ----------
        sv : :class:`ScopedValue`
            A value

        """
        raise NotImplementedError(NO_PROVIDER_ERROR)

    async def delete(self, sv: ScopedValue):
        """
        Delete the given configuration option, matching transport, server, channel, section, and key but
        not value.

        Parameters
        ----------
        sv : :class:`ScopedValue`
            A value

        """
        raise NotImplementedError(NO_PROVIDER_ERROR)


class ScopedConfig:
    """
    Manages the loading of scoped configuration settings and caching them in memory for quick access.

    Attributes
    ----------
    provider : :class:`ScopedConfigProvider`
        The provider, which has to be set by a plugin for configuration values to be settable

    """
    def __init__(self):
        self.values = tree()
        self.provider = ScopedConfigProvider()

        @bus.event('server.ready')
        async def server_ready(server):
            logger.debug("Loading config for transport '{}', server '{}' ({})..."
                         .format(server.transport.id, server.name, server.id))
            for sv in await self.provider.get_all(server):
                self._put(sv)

        @bus.event('server.unready')
        async def server_unready(server):
            logger.debug("Forgetting config for transport '{}', server '{}' ({})..."
                         .format(server.transport.id, server.name, server.id))
            self._clear(server)

    def _put(self, sv: ScopedValue):
        """Puts a :class:`ScopedValue` into the local cache. Does not actually save anything."""

        self.values[sv.transport][sv.server][sv.channel][sv.section][sv.key] = sv

    def _delete(self, sv: ScopedValue):
        """Removes a :class:`ScopedValue` from the local cache."""

        return tree_delete(self.values, (sv.transport, sv.server, sv.channel, sv.section, sv.key))

    def _clear(self, server: Server):
        """Clear all configuration for a server from the local cache."""

        try:
            del self.values[server.transport.id][server.id]
        except KeyError:
            pass

    def _parse_value(self, setting, value):
        try:
            return setting.type(value)
        except Exception:
            return None

    async def put(self, setting: Setting, scope: Union[Server, Channel], value: Optional[str]):
        """
        Store a scoped configuration value.

        Parameters
        ----------
        setting : :class:`Setting`
            The setting
        scope : Union[:class:`Server`, :class:`Channel`]
            The scope
        value : str
            The value to set

        """
        if value is not None:
            # make sure the value is valid
            setting.type(value)

        if isinstance(scope, Channel):
            sv = ScopedValue(scope.transport.id, scope.server.id, scope.id, setting.section, setting.key, value)
        elif isinstance(scope, Server):
            sv = ScopedValue(scope.transport.id, scope.id, None, setting.section, setting.key, value)
        else:
            raise ValueError("{} is not a valid scope (needs to be a Channel or Server)".format(setting))

        if value is not None:
            await self.provider.save(sv)
            self._put(sv)
        else:
            await self.provider.delete(sv)
            self._delete(sv)

    async def delete(self, setting: Setting, scope: Union[Server, Channel]):
        """
        Delete a scoped setting.

        Parameters
        ----------
        setting : :class:`Setting`
            The setting
        scope : Union[:class:`Server`, :class:`Channel`]
            The scope

        """
        return await self.put(setting, scope, None)

    def get_all_server(self, server: Server) -> Sequence[ScopedValue]:
        """
        Get a list of all settings loaded and cached for the given server.

        Parameters
        ----------
        server : :class:`Server`
            The server

        Returns
        -------
        Sequence[ScopedValue]
            A list of set values

        """
        ret = tree_get(self.values, (server.transport.id, server.id, None))
        if ret is not None:
            results = []
            gather_tree_nodes(results, ret)
            return results
        else:
            return []

    def get_all_channel(self, channel: Channel) -> Sequence[ScopedValue]:
        """
        Get a list of all settings loaded and cached for the given channel.

        Parameters
        ----------
        channel : :class:`Channel`
            The channel

        Returns
        -------
        Sequence[ScopedValue]
            A list of set values

        """
        ret = tree_get(self.values, (channel.transport.id, channel.server.id, channel.id))
        if ret is not None:
            results = []
            gather_tree_nodes(results, ret)
            return results
        else:
            return []

    def get_server(self, setting: Setting, server: Server) -> Optional[Any]:
        """
        Get the value set at the server-level for the supplied server, if any.

        Parameters
        ----------
        setting : :class:`Setting`
            The setting
        server : :class:`Server`
            The server

        Returns
        -------
        Optional[Any]
            The value

        """
        sv = tree_get(self.values, (server.transport.id, server.id, None, setting.section, setting.key))
        if sv:
            return self._parse_value(setting, sv.value)
        else:
            return None

    def get_channel(self, setting: Setting, channel: Channel) -> Optional[Any]:
        """
        Get the value set at the channel-level for the supplied channel, if any.

        Parameters
        ----------
        setting : :class:`Setting`
            The setting
        channel : :class:`Channel`
            The channel

        Returns
        -------
        Optional[Any]
            The value

        """
        sv = tree_get(self.values, (channel.transport.id, channel.server.id, channel.id, setting.section, setting.key))
        if sv:
            return self._parse_value(setting, sv.value)
        else:
            return None

    def get(self, setting: Setting, channel: Channel) -> Optional[Any]:
        """
        Get the effective value for the given setting, whether it may be set on the channel, the server,
        or globally from the configuration file.

        Parameters
        ----------
        setting : :class:`Setting`
            The setting
        channel : :class:`Channel`
            The channel

        Returns
        -------
        Optional[Any]
            The value

        """
        value = None

        if not channel.is_private:
            value = self.get_channel(setting, channel)

            # then try the server config
            if value is None:
                value = self.get_server(setting, channel.server)

        # otherwise use global config
        if value is None:
            return setting()

        return value
