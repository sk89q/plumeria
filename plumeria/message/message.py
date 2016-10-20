import logging
from collections import deque
from typing import Union, Optional, List, Dict, Sequence

from plumeria.message.attachment import *
from plumeria.transport import Channel
from plumeria.transport import Server

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
    transport : :class:`Transport`
        The transport that this message belongs to
    edited_timestamp : Optional[:class:`datetime.datetime`]
        A naive UTC datetime object containing the edited time of the message.
    timestamp : :class:`datetime.datetime`
        A naive UTC datetime object containing the time the message was created.
    tts : bool
        Specifies if the message was done with text-to-speech.
    author
        A :class:`Member` that sent the message. If :attr:`channel` is a
        private channel, then it is a :class:`User` instead.
    content : str
        The actual contents of the message.
    embeds : list
        A list of embedded objects. The elements are objects that meet oEmbed's specification_.

        .. _specification: http://oembed.com/
    channel
        The :class:`Channel` that the message was sent from.
    server : Optional[:class:`Server`]
        The server that the message belongs to. If not applicable (i.e. a PM) then it's None instead.
    call: Optional[:class:`CallMessage`]
        The call that the message refers to. This is only applicable to messages of type
        :attr:`MessageType.call`.
    mention_everyone : bool
        Specifies if the message mentions everyone.

        .. note::

            This does not check if the ``@everyone`` text is in the message itself.
            Rather this boolean indicates if the ``@everyone`` text is in the message
            **and** it did end up mentioning everyone.

    mentions: list
        A list of :class:`Member` that were mentioned. If the message is in a private message
        then the list will be of :class:`User` instead. For messages that are not of type
        :attr:`MessageType.default`\, this array can be used to aid in system messages.
        For more information, see :attr:`system_content`.

        .. warning::

            The order of the mentions list is not in any particular order so you should
            not rely on it.

    channel_mentions : list
        A list of :class:`Channel` that were mentioned. If the message is in a private message
        then the list is always empty.
    role_mentions : list
        A list of :class:`Role` that were mentioned. If the message is in a private message
        then the list is always empty.
    id : str
        The message ID.
    attachments : list
        A list of attachments given to a message.
    pinned: bool
        Specifies if the message is currently pinned.
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
        """
        Response to the message.

        Parameters
        ----------
        response : Union[str, :class:`Response`]
            The response

        Returns
        -------
        :class:`Message`
            The message that was sent

        """
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
        self.transport = None
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
    """Used to wrap a message and allow changing some attributes."""

    def __init__(self, message):
        super().__init__()
        self.delegate = message

    async def respond(self, content):
        return await self.delegate.respond(content)

    def __getattr__(self, item):
        return getattr(self.delegate, item)


class Response:
    """
    Represents the response from an executed command.

    Attributes
    ----------
    content : str
        Content of the message
    attachments : Optional[List[:class:`Attachment`]]
        List of attachments to respond with
    registers : Optional[Dict[str, :class:`Message`]]
        Set of registers
    stack : Optional[Sequence[:class:`Message`]]
        List of entries in the stack
    private : bool
        If true, the respond should be sent in a private message if it would normally go to a public or group channel

    """

    def __init__(self, content: str = "", attachments: Optional[List[Attachment]] = None,
                 registers: Optional[Dict[str, Message]] = None, stack: Optional[Sequence[Message]] = None,
                 private: bool = False):
        self.content = content
        self.attachments = attachments or []
        self.registers = registers
        self.stack = stack
        self.private = private
