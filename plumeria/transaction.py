import logging

import pylru

from plumeria.event import bus
from plumeria.message import Message

logger = logging.getLogger(__name__)


class Response:
    def __init__(self, tx, response_message):
        self.transaction = tx
        self.message = response_message
        self.edit_aware = False
        self.delete_aware = False

    async def handle_request_delete(self):
        if not self.delete_aware:
            await self.message.server.transport.edit_message(self.message,
                                                             "Original message by **{}** deleted".format(
                                                                 self.transaction.request_message.author.mention))
            self.delete_aware = True

    async def handle_request_edit(self):
        if not self.edit_aware:
            await self.message.server.transport.edit_message(self.message,
                                                             "Original message by **{}** edited".format(
                                                                 self.transaction.request_message.author.mention))
            self.edit_aware = True


class Transaction:
    def __init__(self, request_message):
        self.request_message = request_message
        self.responses = []


class TransactionLog:
    def __init__(self):
        self.cache = pylru.lrucache(400)

    def get_key(self, message: Message):
        return str(message.channel.transport.id) + ":" + str(message.id)

    def add_response(self, message, response):
        if message.channel.is_private:
            return # not tracking private channels right now
        key = self.get_key(message)
        if key not in self.cache:
            tx = Transaction(message)
            self.cache[key] = tx
        else:
            tx = self.cache[key]
        tx.responses.append(Response(tx, response))

    def get_transaction(self, message):
        try:
            return self.cache[self.get_key(message)]
        except KeyError:
            return None


tx_log = TransactionLog()


@bus.event("message.delete")
async def on_message_delete(message):
    transaction = tx_log.get_transaction(message)
    if transaction:
        for message in transaction.responses:
            try:
                await message.handle_request_delete()
            except:
                # todo: what if one of the responses was deleted?
                logger.warn("Failed to handle deletion of a message", exc_info=True)


@bus.event("message.edit")
async def on_message_edit(before, after):
    transaction = tx_log.get_transaction(before)
    if transaction:
        for message in transaction.responses:
            try:
                await message.handle_request_edit()
            except:
                logger.warn("Failed to handle edit of a message", exc_info=True)
