import re
import socket

from IPy import IP
from aiohttp.resolver import DefaultResolver

ADDRESS_PATTERN = re.compile("^(.+?)(?::([0-9]+))?$")


class InvalidAddress(Exception):
    pass


class NameResolver(DefaultResolver):
    def filter_hosts(self, host):
        ip = IP(host['host'])
        if ip.iptype() == "PUBLIC":
            return True
        else:
            return False

    async def resolve(self, host, port=0, family=socket.AF_INET):
        hosts = await super().resolve(host, port, family)
        hosts = list(filter(self.filter_hosts, hosts))
        if not len(hosts):
            raise socket.gaierror("no public ip returned")
        return hosts

    async def resolve_ip(self, host, port=0, family=socket.AF_INET):
        hosts = await self.resolve(host, port, family)
        return hosts[0]['host']


class AddressResolver:
    def __init__(self, name_resolver=None, port_validator=lambda p: True):
        self.name_resolver = name_resolver or NameResolver()
        self.port_validator = port_validator

    async def resolve(self, s, default_port):
        m = ADDRESS_PATTERN.match(s)
        if m:
            try:
                host = await self.name_resolver.resolve_ip(m.group(1))
            except OSError as e:
                raise InvalidAddress("Failed to resolve address.")
            port = int(m.group(2)) if m.group(2) else default_port
            if port < 1 or port > 65535:
                raise InvalidAddress("Invalid port number.")
            if not self.port_validator(port):
                raise InvalidAddress("Port number is not within the valid range.")
            return host, port
        raise InvalidAddress("The address is unrecognized.")
