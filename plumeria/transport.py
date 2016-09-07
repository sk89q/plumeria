class TransportManager:
    def __init__(self):
        self.transports = {}

    def register(self, name, transport):
        self.transports[name] = transport


class Transport:
    pass


class User:
    pass


class Member:
    pass


class Role:
    pass


transports = TransportManager()
