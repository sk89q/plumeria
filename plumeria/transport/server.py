class Server:
    """
    Represents a server.
    """

    def __eq__(self, other):
        return isinstance(other, Server) and self.transport == other.transport and self.id == other.id
