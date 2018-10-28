"""Creating bot object."""

import logging
import asyncio

import aiogram
import aiogram.types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from recrierbot.domain import DomainRoot
from recrierbot.settings import BotSettings

from . import routes
from .communicator import BotCommunicator


async def make_bot(settings: BotSettings, domain: DomainRoot) -> BotCommunicator:
    proxy = None
    if settings.socks5_proxy is not None:
        proxy = settings.socks5_proxy
        logging.warning(f'Using socks5_proxy {proxy!r} for Telegram API.')

    bot = aiogram.Bot(settings.telegram_token, proxy=proxy)
    state_storage = MemoryStorage()
    dispatcher = aiogram.Dispatcher(bot, storage=state_storage)

    routes.check_in(dispatcher, domain, settings.base_bot_url)

    hook_token = None

    if settings.base_bot_url:
        hook_token = _generate_hook_token()
        hook_url = settings.base_bot_url + hook_token + '/hook'
        logging.warning(f'Base bot URL is provided. Web hook URL: {hook_url!r}')
        logging.warning('Settings web hook...')
        await bot.set_webhook(hook_url)
        logging.warning('Web hook is set')
    else:
        # FIXME: Starting polling as a coroutine. Can this fail somehow? Who nose...
        logging.warning('Base bot URL is not provided. Using polling.')
        asyncio.create_task(dispatcher.start_polling(reset_webhook=True))
        logging.warning('Polling task was created.')

    return BotCommunicator(bot, dispatcher, settings, hook_token=hook_token)


def _generate_hook_token():
    from uuid import uuid4
    return uuid4().hex
