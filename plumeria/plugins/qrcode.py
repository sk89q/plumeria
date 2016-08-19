import asyncio

import qrcode
from PIL import Image
from plumeria.command import commands, CommandError
from plumeria.message import Response, ImageAttachment
from plumeria.util.ratelimit import rate_limit


@commands.register('qrcode', 'qr', category='Image')
@rate_limit(burst_size=2)
async def qr(message):
    if len(message.content) > 200:
        raise CommandError("Text is too long to generate a QR code for.")

    """
    Generates a QR code from given text.
    """
    def execute():
        old = qrcode.make(message.content, border=2)
        new = Image.new("RGB", old.size, (255, 255, 255))
        new.paste(old)
        return new

    im = await asyncio.get_event_loop().run_in_executor(None, execute)
    return Response("", [ImageAttachment(im, "qr.png")])
