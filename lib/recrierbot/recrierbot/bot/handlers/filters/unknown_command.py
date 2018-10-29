from aiogram import Bot
from aiogram.types import Message, ChatType
from aiogram.dispatcher.filters import AsyncFilter


class UnknownCommand(AsyncFilter):

    # FIXME: hardcode...
    _known_commands = ['start', 'newtoken', 'deltoken', 'listtokens', 'ping']

    def __init__(self, bot: Bot):
        self._bot = bot

    async def check(self, message: Message):
        if not message.is_command():
            return False

        command = message.text.split()[0][1:]
        command, _, mention = command.partition('@')

        if mention and mention != (await self._bot.me).username:
            return False

        if message.chat.type != ChatType.PRIVATE and not mention:
            return False

        if command in self._known_commands:
            return False

        return True
