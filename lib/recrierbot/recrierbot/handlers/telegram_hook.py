from aiohttp.web import Request, Response
from recrierbot.bot import BotCommunicator


class TelegramHookHandler(object):

    def __init__(self, bot: BotCommunicator):
        self._bot = bot

    async def __call__(self, request: Request):
        if request.match_info.get('hook_token') != self._bot.hook_token:
            return Response(status=403)

        self._bot.process_update(await request.json())
        return Response(status=200)
