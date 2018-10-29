"""Start command handler."""

from aiogram import Dispatcher
from aiogram.types import Message

from .filters import CommandFilter


def handler_start(dispatcher: Dispatcher):
    bot = dispatcher.bot

    @dispatcher.message_handler(CommandFilter(bot, 'start'))
    async def handle_start(message: Message):
        await bot.send_message(chat_id=message.chat.id, text='Hi. Use /newtoken to generate a new token.')
