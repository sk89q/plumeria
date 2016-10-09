from typing import Dict


class TransportManager:
    def __init__(self):
        self.transports = {}  # type: Dict[str, Transport]

    def register(self, name, transport):
        self.transports[name] = transport


class Transport:
    """
    Represents an incoming source of messages and outgoing sink for responses.
    """

    def _ide_hint(self):
        # fix unresolved attribute errors
        self.id = None
        self.user = None
        self.voice_clients = None
        self.servers = None
        self.private_channels = None
        self.is_logged_in = None
        self.is_closed = None
