"""Token related handlers."""

from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.types import ParseMode
from aiogram.utils.emoji import emojize

from recrierbot.domain import DomainRoot
from .filters import CommandFilter


def handler_tokens(dispatcher: Dispatcher, domain: DomainRoot, base_bot_url: str = None):
    bot = dispatcher.bot

    @dispatcher.message_handler(CommandFilter(bot, 'newtoken'))
    async def handle_newtoken(message: Message):
        tokens_for_chat = await domain.tokens.find_tokens(message.chat.id)

        if len(tokens_for_chat) >= domain.settings.user_tokens_limit:
            await bot.send_message(
                message.chat.id,
                text=f'Limit of tokens of {domain.settings.user_tokens_limit} is exceeded. '
                     f'Use /listtokens to see all of your tokens.'
            )
            return

        new_token = await domain.tokens.create(message.chat.id)
        text = f'Here\'s your new token: `{new_token}`'

        # If it is None we do not know public bot url
        if base_bot_url is not None:
            url_template = base_bot_url + new_token + '/send'
            text += f'Url template: `{url_template}`'

        await bot.send_message(
            message.chat.id,
            text=text,
            parse_mode=ParseMode.MARKDOWN
        )

    @dispatcher.message_handler(CommandFilter(bot, 'listtokens'))
    async def handle_listtokens(message: Message):
        tokens = await domain.tokens.find_tokens(message.chat.id)
        if not tokens:
            text = 'No tokens are created.'
        else:
            text = 'Tokens for this chat:\n' + '\n'.join((f'`{token}`' for token in tokens))

        await bot.send_message(message.chat.id, text, parse_mode=ParseMode.MARKDOWN)

    @dispatcher.message_handler(CommandFilter(bot, 'deltoken'))
    async def handle_deltoken(message: Message):
        token_values_to_delete = message.get_args().split()
        if not token_values_to_delete:
            await bot.send_message(message.chat.id,
                                   'Give me tokens to delete: \n'
                                   '\\deltoken a1Bd3f 7ab1cd ...')
            return

        await domain.tokens.delete(token_values_to_delete, chat_id=message.chat.id)
        await bot.send_message(message.chat.id, emojize('Done. :heavy_check_mark:'))
