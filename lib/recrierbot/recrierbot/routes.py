from aiohttp.web import Application, get, post
from recrierbot.bot import BotCommunicator
from recrierbot.domain import DomainRoot

from .handlers import TelegramHookHandler, StatusHandler, SendMessageHandler, IndexHandler


def make_aiohttp_routes(app: Application,
                        bot: BotCommunicator,
                        domain: DomainRoot
                        ):

    handle_telegram_hook = TelegramHookHandler(bot)
    handle_status = StatusHandler()
    handle_send_message = SendMessageHandler(bot, domain)
    handle_index = IndexHandler(bot)

    app.add_routes([
        # Telegram callback
        post('/{hook_token}/hook', handle_telegram_hook, name='telegram_hook'),

        # User API
        get('/{user_token}/send', handle_send_message, name='user_send'),
        post('/{user_token}/send', handle_send_message, name='user_send'),

        # User Web
        get('/status', handle_status, name='status'),
        get('/', handle_index, name='index'),
    ])
