TEXT_TYPE = 'text'
VOICE_TYPE = 'voice'


class Channel:
    def is_default_channel(self):
        return self.server.get_default_channel() == self

    def mention(self):
        return "#{}".format(self.name)

    async def send_file(self, fp, filename=None, content=None):
        raise NotImplemented()

    async def send_message(self, content, tts=False):
        raise NotImplemented()

    async def get_history(self, limit=100):
        raise NotImplemented()
