from typing import Dict


class ForbiddenError(Exception):
    """Raised when the bot can't do something."""


class TransportManager:
    def __init__(self):
        self.transports = {}  # type: Dict[str, Transport]

    def register(self, name, transport):
        self.transports[name] = transport


class Transport:
    """
    Represents an incoming source of messages and outgoing sink for responses.
    """

    def resolve_user(self, q, hint=None, domain=None):
        """
        Resolves a string to a user.

        Parameters
        ----------
        q : str
            The username to find.
        hint : Optional[:class:`plumeria.transport.User`]
            A list of users to first try searching from.
        domain : Optional[:class:`plumeria.transport.User`]
            A list of users to search exclusively from.

        Returns
        -------
        Optional[:class:`plumeria.transport.User`]
            A user if one is found.
        """

        raise NotImplementedError("not implemented")

    def _ide_hint(self):
        # fix unresolved attribute errors
        self.id = None
        self.user = None
        self.voice_clients = None
        self.servers = None
        self.private_channels = None
        self.is_logged_in = None
        self.is_closed = None
