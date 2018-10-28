from aiogram.bot import Bot
from aiogram.types import Message, ChatType
from aiogram.dispatcher.filters import AsyncFilter


class CommandFilter(AsyncFilter):
    """
    Check commands in message.
    Alternative to aiogram built-in commands filter
    """

    def __init__(self, bot: Bot, *commands: str):
        self._commands = commands
        self._bot = bot

    async def check(self, message: Message):
        if not message.is_command():
            return False

        command = message.text.split()[0][1:]
        command, _, mention = command.partition('@')

        import logging
        if mention and mention != (await self._bot.me).username:
            logging.warning(f'denied command because I got mention and mention {mention!r} and it is not my username')
            return False

        if message.chat.type == ChatType.GROUP and not mention:
            logging.warning(f'denied command because I got no mention but chat is a group chat')
            return False

        if command not in self._commands:
            return False

        return True
