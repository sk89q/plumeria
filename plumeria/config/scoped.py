import logging
from typing import Optional, Union, Sequence

from plumeria.config import Setting
from plumeria.event import bus
from plumeria.transport import Channel
from plumeria.transport import Server
from plumeria.util.collections import tree, tree_get, tree_delete, gather_tree_nodes

logger = logging.getLogger(__name__)

NO_PROVIDER_ERROR = "A plugin that allows the bot to save these configuration values somewhere (like to a database) " \
                    "needs to be enabled."


class ScopedValue:
    """Holds a scoped configuration value."""

    __slots__ = ('transport', 'server', 'channel', 'section', 'key', 'value')

    def __init__(self, transport: str, server: str, channel: Optional[str], section: str, key: str, value: str):
        self.transport = transport
        self.server = server
        self.channel = channel
        self.section = section
        self.key = key
        self.value = value


class ScopedConfigProvider:
    async def get_all(self, server: Server) -> Sequence[ScopedValue]:
        return []

    async def save(self, sv: ScopedValue):
        raise NotImplementedError(NO_PROVIDER_ERROR)

    async def delete(self, sv: ScopedValue):
        raise NotImplementedError(NO_PROVIDER_ERROR)


class ScopedConfig:
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
        return await self.put(setting, scope, None)

    def get_all_server(self, server: Server):
        ret = tree_get(self.values, (server.transport.id, server.id, None))
        if ret is not None:
            results = []
            gather_tree_nodes(results, ret)
            return results
        else:
            return []

    def get_all_channel(self, channel: Channel):
        ret = tree_get(self.values, (channel.transport.id, channel.server.id, channel.id))
        if ret is not None:
            results = []
            gather_tree_nodes(results, ret)
            return results
        else:
            return []

    def get_server(self, setting: Setting, server: Server):
        sv = tree_get(self.values, (server.transport.id, server.id, None, setting.section, setting.key))
        if sv:
            return self._parse_value(setting, sv.value)
        else:
            return None

    def get_channel(self, setting: Setting, channel: Channel):
        sv = tree_get(self.values, (channel.transport.id, channel.server.id, channel.id, setting.section, setting.key))
        if sv:
            return self._parse_value(setting, sv.value)
        else:
            return None

    def get(self, setting: Setting, channel: Channel):
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
