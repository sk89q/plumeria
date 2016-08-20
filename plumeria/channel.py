class Channel:
    def __init__(self, name, server, id, topic, is_private, position, type, bitrate, voice_members, user_limit, is_default, mention, created_at):
        self.name = name
        self.server = server
        self.id = id
        self.topic = topic
        self.is_private = is_private
        self.position = position
        self.type = type
        self.bitrate = bitrate
        self.voice_members = voice_members
        self.user_limit = user_limit
        self.is_default = is_default
        self.mention = mention
        self.created_at = created_at

    async def send_file(self, fp, filename=None, content=None):
        raise NotImplemented()

    async def send_message(self, content, tts=False):
        raise NotImplemented()

    async def get_history(self, limit=100):
        raise NotImplemented()
