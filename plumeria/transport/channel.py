TEXT_TYPE = 'text'
VOICE_TYPE = 'voice'


class Channel:
    """
    Represents a channel.
    """

    def __eq__(self, other):
        return isinstance(other, Channel) and self.server == other.server and self.id == other.id

    def _ide_hint(self):
        # fix unresolved attribute errors
        self.id = None
        self.name = None
        self.server = None
        self.topic = None
        self.is_private = None
        self.position = None
        self.type = None
        self.bitrate = None
        self.voice_members = None
        self.user_limit = None
        self.changed_roles = None
        self.is_default = None
        self.created_at = None
