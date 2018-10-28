from aiogram.types import ParseMode
from aiogram.utils.exceptions import TelegramAPIError
from aiohttp.web import Request, json_response
from recrierbot.domain import DomainRoot
from recrierbot.bot import BotCommunicator


class SendMessageHandler(object):

    def __init__(self, bot: BotCommunicator, domain: DomainRoot):
        self._bot = bot
        self._domain = domain

    async def __call__(self, request: Request):
        if request.method == 'GET':
            data = request.query
            if not data:
                return json_response({'result': 'error', 'error': 'no_data_provided'})
        elif request.method == 'POST':
            try:
                data = await request.json()
            except Exception:
                return json_response({'result': 'error', 'error': 'no_data_provided'})
        else:
            return json_response({'result': 'error', 'error': 'method_not_allowed'}, status=405)

        token = request.match_info.get('user_token')
        if token is None:
            return json_response({'result': 'error', 'error': 'empty_token'}, status=403)

        mode = data.get('mode', None)
        if mode not in [None, 'markdown', 'html']:
            return json_response({'result': 'error', 'error': 'unknown_message_mode', 'mode': mode}, status=400)

        message = data.get('message')
        if not message:
            return json_response({'result': 'error', 'error': 'empty_message'}, status=400)

        chat_id = await self._domain.tokens.find_chat_id(token)
        if not chat_id:
            return json_response({'result': 'error', 'error': 'bad_token'}, status=400)

        if mode:
            mode = getattr(ParseMode, mode.upper())

        try:
            await self._bot.bot.send_message(chat_id, text=message, parse_mode=mode)
            return json_response({'result': 'ok'}, status=200)
        except TelegramAPIError:
            return json_response({'result': 'error', 'error': 'telegram_send_message_failed'}, status=500)
