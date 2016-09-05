import asyncio
import io
import logging
import math
import os
import os.path
import shutil
import subprocess
from tempfile import mkdtemp

from PIL import Image

from plumeria.command import commands, CommandError
from plumeria.message import Response, MemoryAttachment
from plumeria.util.message import read_image
from plumeria.util.ratelimit import rate_limit

VTFCMD_PATH = os.path.join("bin", "VTFCmd.exe")

logger = logging.getLogger(__name__)


def resize_canvas(im, size):
    canvas_width, canvas_height = size
    old_width, old_height = im.size
    x1 = int(math.floor((canvas_width - old_width) / 2))
    y1 = int(math.floor((canvas_height - old_height) / 2))

    resized = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 0))
    resized.paste(im, (x1, y1, x1 + old_width, y1 + old_height))
    return resized


@commands.register('make spray', 'makespray', category='Image')
@rate_limit(burst_size=2)
async def make_spray(message):
    """
    Creates a Source engine spray from an image.

    Example::

        /drawtext Hello there! | make spray

    You can also upload an image as an attachment and then use this command.
    """

    if not os.path.exists(VTFCMD_PATH):
        raise IOError("Cannot find VTFCmd (tried {})".format(VTFCMD_PATH))

    attachment = await read_image(message)
    if not attachment:
        raise CommandError("No image is available to process.")

    im = attachment.image

    def execute():
        w, h = im.size
        if w >= 512 or h >= 512:
            dim = 512
        elif w >= 256 or h >= 256:
            dim = 256
        elif w >= 128 or h >= 128:
            dim = 128
        else:
            dim = 64

        im.thumbnail((dim, dim), Image.LANCZOS)
        final = resize_canvas(im, (dim, dim))

        temp_dir = mkdtemp()
        try:
            image_file = os.path.join(temp_dir, "spray.png")
            vtf_file = os.path.join(temp_dir, "spray.vtf")

            with open(image_file, "wb") as f:
                final.save(f, "PNG")

            args = []
            if os.name != 'nt':
                args.append("wine")
            args.append(os.path.realpath(VTFCMD_PATH))
            args.append("-nomipmaps")
            args.append("-format")
            args.append("dxt5")
            args.append("-alphaformat")
            args.append("dxt5")
            args.append("-nothumbnail")
            args.append("-noreflectivity")
            args.append("-file")
            args.append(os.path.realpath(image_file))
            p = subprocess.Popen(args, cwd=os.path.dirname(vtf_file),
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate(timeout=10)

            if p.returncode == 0:
                if os.path.exists(vtf_file):
                    logger.debug("VTFCmd ran successfully:\n\nstderr: {}\n\nstdout: {}".format(
                        stderr.decode("utf-8", errors='ignore'),
                        stdout.decode("utf-8", errors='ignore')
                    ))
                    buffer = io.BytesIO()
                    with open(vtf_file, "rb") as f:
                        buffer.write(f.read())
                    return buffer
                else:
                    logger.warn("VTFCmd failed to create a file:\n\nargs: {}\nreturn code {}\nfiles:{}\n\nstderr: {}\n\nstdout: {}".format(
                        " ".join(args),
                        p.returncode,
                        " ".join(os.listdir(temp_dir)),
                        stderr.decode("utf-8", errors='ignore'),
                        stdout.decode("utf-8", errors='ignore')
                    ))
                raise CommandError("Failed to create spray (the bot administrator can see the logs)")
            else:
                logger.warn("VTFCmd failed to run:\n\nargs: {}\nreturn code {}\n\nstderr: {}\n\nstdout: {}".format(
                    " ".join(args),
                    p.returncode,
                    stderr.decode("utf-8", errors='ignore'),
                    stdout.decode("utf-8", errors='ignore')
                ))
                raise CommandError("Failed to create spray (bad error code)")
        finally:
            shutil.rmtree(temp_dir)

    output = await asyncio.get_event_loop().run_in_executor(None, execute)
    return Response("", [MemoryAttachment(output, "spray.vtf", "application/octet-stream")])
