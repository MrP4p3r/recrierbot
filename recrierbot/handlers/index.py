from aiohttp.web import Request, Response
from recrierbot.bot import BotCommunicator
from .templates import render


class IndexHandler(object):

    def __init__(self, bot: BotCommunicator):
        self._bot = bot

    async def __call__(self, request: Request):
        data = {
            'bot_username': await self._bot.get_bot_username(),
            'bot_url': request.url.origin(),
        }

        return Response(
            text=render('index', data),
            content_type='text/html',
        )
