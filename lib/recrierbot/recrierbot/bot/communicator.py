import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import ParseMode, Update
from recrierbot.settings import BotSettings


class BotCommunicator(object):

    def __init__(self,
                 bot: Bot,
                 dispatcher: Dispatcher,
                 settings: BotSettings,
                 hook_token: str):
        self._bot = bot
        self._dispatcher = dispatcher
        self._hook_token = hook_token
        self._settings = settings

    @property
    def hook_token(self) -> str:
        return self._hook_token

    def process_update(self, update_dict: dict):
        update = Update(**update_dict)
        asyncio.create_task(self._dispatcher.process_update(update))

    async def send_message(self, chat_id: int, text: str, parse_mode: str):
        if parse_mode:
            parse_mode = getattr(ParseMode, parse_mode.upper())

        await self._bot.send_message(chat_id, text=text, parse_mode=parse_mode)

    async def get_bot_username(self) -> str:
        return (await self._bot.me).username

    async def get_base_url(self) -> str:
        return self._settings.base_bot_url
