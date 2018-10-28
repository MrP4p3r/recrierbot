"""Generic message handlers."""

import logging

from aiogram import Dispatcher
from aiogram.types import Message, Update
from aiogram.utils.emoji import emojize
from aiogram.dispatcher.filters import Filter, AnyFilter


class NotCommandFilter(Filter):

    def check(self, obj):
        return bool(isinstance(obj, Message) and not obj.is_command())


class UnknownCommand(Filter):

    known_commands = ['start', 'newtoken', 'deltoken', 'listtokens', 'ping']

    def check(self, obj):
        return bool(isinstance(obj, Message)
                    and obj.is_command()
                    and obj.get_command(pure=True) not in self.known_commands)


def handler_generic(dispatcher: Dispatcher):
    bot = dispatcher.bot

    @dispatcher.message_handler(commands=['ping'])
    async def handle_ping(message: Message):
        await bot.send_message(message.chat.id, emojize('Pong :wink:'))

    @dispatcher.message_handler(AnyFilter(NotCommandFilter(), UnknownCommand()))
    async def msg_handler(message: Message):
        await bot.send_message(message.chat.id, emojize('What? :sweat_smile:'))

    @dispatcher.errors_handler()
    async def error_handler(_, update: Update, exc: BaseException):
        logging.exception('Something went wrong...')
        await bot.send_message(update.message.chat.id, 'Something went wrong :-0')
