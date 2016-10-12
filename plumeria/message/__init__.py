import asyncio
import io
import logging
from collections import deque

from PIL import Image

from plumeria.transport import Channel
from plumeria.transport import Server
from plumeria.util.http import DefaultClientSession

MAX_BODY_LENGTH = 1900
MAX_LINES = 50
CONTINUATION_STRING = "\n..."

logger = logging.getLogger(__name__)


def create_stack():
    return deque(maxlen=20)


class Message:
    """
    Represents a message.

    Attributes
    ----------
    direct : bool
        Whether this message is directly from a user (for commands invoked from
        aliases, this is false).

    """

    def __init__(self):
        super().__init__()
        self.registers = {}
        self.stack = create_stack()
        self.direct = False

    async def respond(self, response):
        if not isinstance(response, Response):
            response = Response(response)

        target_channel = self.channel
        redirected = False

        if response.private and not target_channel.is_private:
            target_channel = await self.transport.start_private_message(self.author)
            redirected = True

        if len(response.attachments):
            return await target_channel.send_file(io.BytesIO(await response.attachments[0].read()),
                                                  filename=response.attachments[0].filename,
                                                  content=response.content)
        else:
            body = response.content.strip()
            lines = body.splitlines()

            if len(body) > MAX_BODY_LENGTH or len(lines) > MAX_LINES:
                buffer = io.StringIO()
                current_length = len(CONTINUATION_STRING)
                line_count = 0
                first = True

                for line in lines:
                    line_length = len(line)
                    if current_length + line_length > MAX_BODY_LENGTH or line_count > MAX_LINES - 1:
                        break
                    else:
                        if first:
                            first = False
                        else:
                            buffer.write("\n")
                        buffer.write(line)
                        current_length += line_length
                        line_count += 1

                truncated_body = buffer.getvalue() + CONTINUATION_STRING

                ret = await target_channel.send_file(io.BytesIO(body.encode("utf-8")),
                                                      filename="continued.txt",
                                                      content=truncated_body)
            else:
                ret = await target_channel.send_message(response.content)

        if redirected:
            await self.channel.send_message(
                "You ran a command that sent the results to a private channel, {}.".format(self.author.mention))

        return ret

    def __repr__(self, *args, **kwargs):
        return repr(self.__dict__)

    def __str__(self, *args, **kwargs):
        return repr(self.__dict__)

    def _ide_hint(self):
        # fix unresolved attribute errors
        self.id = None
        self.edited_timestamp = None
        self.timestamp = None
        self.tts = None
        self.type = None
        self.author = None
        self.content = None
        self.nonce = None
        self.embeds = None
        self.channel = None  # type: Channel
        self.server = None  # type: Server
        self.call = None
        self.mention_everyone = None
        self.channel_mentions = None
        self.role_mentions = None
        self.attachments = None
        self.pinned = None
        self.raw_mentions = None
        self.raw_channel_mentions = None
        self.raw_role_mentions = None
        self.clean_content = None
        self.system_content = None


class ProxyMessage:
    def __init__(self, message):
        super().__init__()
        self.delegate = message

    async def respond(self, content):
        return await self.delegate.respond(content)

    def __getattr__(self, item):
        return getattr(self.delegate, item)


class Response:
    def __init__(self, content="", attachments=None, registers=None, stack=None, private=False):
        self.content = content
        self.attachments = attachments or []
        self.registers = registers
        self.stack = stack
        self.private = private


class Attachment:
    url = None
    filename = None
    mime_type = None

    async def read(self):
        raise NotImplemented()

    def copy(self):
        raise NotImplemented()


class MemoryAttachment:
    def __init__(self, bytes, filename, mime_type):
        self.bytes = bytes
        self.filename = filename
        self.mime_type = mime_type

    async def read(self):
        return self.bytes.getvalue()

    def copy(self):
        return self


class URLAttachment:
    def __init__(self, url, filename, mime_type):
        self.url = url
        self.filename = filename
        self.mime_type = mime_type

    async def read(self):
        with DefaultClientSession() as session:
            async with session.get(self.url) as resp:
                if resp.status == 200:
                    return await resp.read()
                else:
                    raise IOError("Did not get 200 status")

    def copy(self):
        return self


class ImageAttachment(Attachment):
    def __init__(self, image: Image, filename):
        self.image = image
        self.filename = filename + ".png"
        self.mime_type = 'image/png'

    async def read(self):
        def execute():
            out = io.BytesIO()
            self.image.save(out, 'png')
            return out.getvalue()

        return await asyncio.get_event_loop().run_in_executor(None, execute)

    def copy(self):
        return ImageAttachment(self.image.copy(), self.filename)
