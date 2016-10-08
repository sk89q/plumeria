TEXT_TYPE = 'text'
VOICE_TYPE = 'voice'


class Channel:
    """
    Represents a channel.
    """

    def __eq__(self, other):
        return isinstance(other, Channel) and self.server == other.server and self.id == other.id
