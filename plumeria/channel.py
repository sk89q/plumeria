class Channel:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    async def send_file(self, fp, filename=None, content=None):
        raise NotImplemented()

    async def send_message(self, content, tts=False):
        raise NotImplemented()

    async def get_history(self, limit=100):
        raise NotImplemented()