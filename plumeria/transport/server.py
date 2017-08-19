class Server:
    """
    Represents a server.
    """

    @property
    def perma_id(self):
        return "{}:{}".format(self.transport.perma_id, self.id)

    def __eq__(self, other):
        return isinstance(other, Server) and self.transport == other.transport and self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def _ide_hint(self):
        # fix unresolved attribute errors
        self.transport = None
        self.id = None
        self.name = None
        self.me = None
        self.roles = None
        self.emojis = None
        self.region = None
        self.afk_timeout = None
        self.afk_channel = None
        self.channels = None
        self.icon = None
        self.owner = None
        self.unavailable = None
        self.large = None
        self.voice_client = None
        self.mfa_level = None
        self.verification_level = None
        self.default_role = None
        self.default_channel = None
        self.icon_url = None
        self.member_count = None
        self.created_at = None
        self.role_hierarchy = None

    async def create_custom_emoji(self, name, image):
        raise NotImplementedError("not implemented")

    async def delete_custom_emoji(self, emoji):
        raise NotImplementedError("not implemented")

    def update(self, **kwargs):
        raise NotImplementedError("not implemented")
