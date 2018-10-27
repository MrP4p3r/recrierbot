"""Start command handler."""

from aiogram import Dispatcher
from aiogram.types import Message


def handler_start(dispatcher: Dispatcher):
    bot = dispatcher.bot

    @dispatcher.message_handler(commands=['start'])
    async def handle_start(message: Message):
        await bot.send_message(chat_id=message.chat.id, text='Hi. Use /newtoken to generate a new token.')
