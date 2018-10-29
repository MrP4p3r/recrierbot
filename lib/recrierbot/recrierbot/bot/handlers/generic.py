"""Generic message handlers."""

import logging

from aiogram import Dispatcher
from aiogram.types import Message, Update
from aiogram.utils.emoji import emojize
from aiogram.dispatcher.filters import AnyFilter

from .filters import CommandFilter, NotCommandFilter, UnknownCommand


def handler_generic(dispatcher: Dispatcher):
    bot = dispatcher.bot

    @dispatcher.message_handler(CommandFilter(bot, 'ping'))
    async def handle_ping(message: Message):
        await bot.send_message(message.chat.id, emojize('Pong :wink:'))

    @dispatcher.message_handler(AnyFilter(NotCommandFilter(bot), UnknownCommand(bot)))
    async def msg_handler(message: Message):
        await bot.send_message(message.chat.id, emojize('What? :sweat_smile:'))

    @dispatcher.errors_handler()
    async def error_handler(_, update: Update, exc: BaseException):
        logging.exception('Something went wrong...')
        await bot.send_message(update.message.chat.id, 'Something went wrong :-0')
