"""Classes representing attachments added on messages and responses."""

import asyncio

import io
from typing import Awaitable

from PIL import Image

from plumeria.util.http import DefaultClientSession


class Attachment:
    """
    Holds information and data for an attachment.

    Attributes
    ----------
    url : Optional[str]
        The URL of the attachment, if one exists
    filename : str
        Filename of the file
    mime_type : str
        Mime-type of the file

    """

    url = None
    filename = None
    mime_type = None

    async def read(self) -> Awaitable[bytes]:
        """
        Return the bytes of the file.

        Returns
        -------
        Awaitable[bytes]
            The file's data

        """
        raise NotImplemented()

    def copy(self):
        """
        Create a copy of the attachment.

        Returns
        -------
        :class:`Attachment`
            A new attachment object

        """
        raise NotImplemented()


class MemoryAttachment:
    """An attachment with the contents of the file stored in memory."""

    def __init__(self, bytes, filename, mime_type):
        self.bytes = bytes
        self.filename = filename
        self.mime_type = mime_type

    async def read(self):
        return self.bytes.getvalue()

    def copy(self):
        return self


class URLAttachment:
    """An attachment that must be fetched from a URL."""

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
    """A PIL Image attachment."""

    def __init__(self, image: Image, filename):
        self.image = image
        self.filename = filename + ".png"
        self.mime_type = 'image/png'

    async def read(self):
        def execute():
            out = io.BytesIO()
            if self.mime_type == 'image/jpeg':
                self.image.save(out, 'jpeg')
            else:
                self.image.save(out, 'png')
            return out.getvalue()

        return await asyncio.get_event_loop().run_in_executor(None, execute)

    def copy(self):
        return ImageAttachment(self.image.copy(), self.filename)
