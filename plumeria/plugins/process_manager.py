import asyncio
import logging

import sys

import psutil as psutil

from plumeria import config
from plumeria.channel import TEXT_TYPE
from plumeria.command import commands, CommandError
from plumeria.perms import roles_only
from plumeria.util.command import add_doc
from plumeria.transport import transports

name = config.create("process_manager", "name",
                     fallback="arma3",
                     comment="The command prefix")

desc = config.create("process_manager", "description",
                     fallback="Arma 3",
                     comment="The command prefix")

cmd = config.create("process_manager", "cmd",
                    fallback="",
                    comment="The process to run")

working_dir = config.create("process_manager", "working_dir",
                            fallback="",
                            comment="The working directory of the process")

roles = config.create("process_manager", "required_roles",
                      fallback="admin,control-example",
                      comment="A comma-separated list of roles that can control this process")

notification_chans = config.create("process_manager", "channels",
                                   fallback="",
                                   comment="A comma-separated list of channels, if any, to receive notifications")

logger = logging.getLogger(__name__)


async def send_notifications(content):
    # kind of slow but we don't call this often, and hopefully the list is small
    matching = set(map(lambda s: s.strip().lower().replace("#", ""), notification_chans().split(",")))
    for transport in transports.transports.values():
        for server in transport.servers:
            for channel in server.channels:
                if channel.type == TEXT_TYPE and channel.name.lower() in matching:
                    await channel.send_message(content)


class ProcessWrapper(asyncio.SubprocessProtocol):
    def __init__(self, process_manager):
        self.process_manager = process_manager

    def pipe_data_received(self, fd, data):
        if fd == 1:
            sys.stdout.buffer.write(data)  # note: blocking
        elif fd == 2:
            sys.stderr.buffer.write(data)  # note: blocking

    def process_exited(self):
        asyncio.get_event_loop().create_task(self.process_manager.on_process_exited())


class ProcessManager:
    def __init__(self):
        self.process = None

    async def start(self):
        if self.process:
            raise ValueError("Process is already started")
        args = cmd()
        self.process, protocol = await asyncio.get_event_loop().subprocess_shell(
            lambda: ProcessWrapper(self),
            args,
            cwd=working_dir())
        return self.process

    async def kill(self):
        if not self.process:
            raise ValueError("Process isn't running")

        logger.info("Process '{}' is being killed...".format(desc()))
        pid = self.process.get_pid()

        def execute():
            parent = psutil.Process(pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()

        return await asyncio.get_event_loop().run_in_executor(None, execute)

    async def on_process_exited(self):
        return_code = self.process.get_returncode()
        self.process = None
        logger.info("Process '{}' exited!".format(desc()))
        await send_notifications(
            ":warning: Process **{}** exited with return code **{}**".format(desc(), return_code))


if len(cmd()):
    process_manager = ProcessManager()


    @commands.register(*map(lambda s: s.format(name()), ("{} start",)), category="Control")
    @add_doc("Starts {} if it isn't started yet.".format(desc()))
    @roles_only(*filter(lambda r: len(r), map(lambda r: r.strip(), roles().split(","))))
    async def start(message):
        try:
            await process_manager.start()
            return ":ok: Successfully started **{}**".format(desc())
        except Exception as e:
            logging.warning("Failed to start process", exc_info=True)
            raise CommandError("Failed to start '{}': {}".format(desc(), str(e)))


    @commands.register(*map(lambda s: s.format(name()), ("{} status", "{} stat")), category="Control")
    @add_doc("Checks the status of {}.".format(desc()))
    @roles_only(*filter(lambda r: len(r), map(lambda r: r.strip(), roles().split(","))))
    async def status(message):
        if process_manager.process:
            return "**{}** is currently running :ok:".format(desc())
        else:
            return "**{}** is not running :octagonal_sign:".format(desc())


    @commands.register(*map(lambda s: s.format(name()), ("{} kill", "{} terminate")), category="Control")
    @add_doc("Kills {} if it is running.".format(desc()))
    @roles_only(*filter(lambda r: len(r), map(lambda r: r.strip(), roles().split(","))))
    async def kill(message):
        try:
            await process_manager.kill()
            return "Killed **{}**".format(desc())
        except Exception as e:
            logging.warning("Failed to kill process", exc_info=True)
            raise CommandError("Failed to kill '{}': {}".format(desc(), str(e)))
else:
    logger.info("Process manager plugin is enabled but it is not configured")
