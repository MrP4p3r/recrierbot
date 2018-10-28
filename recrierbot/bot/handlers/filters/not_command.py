from aiogram.types import Message, ChatType
from aiogram.dispatcher.filters import AsyncFilter


class NotCommandFilter(AsyncFilter):

    def __init__(self, bot):
        self._bot = bot

    async def check(self, message: Message):
        if message.is_command():
            return False

        if message.chat.type != ChatType.PRIVATE and ('@' + (await self._bot.me).username) in message.text.split():
            return False

        return True
