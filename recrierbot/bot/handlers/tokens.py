"""Token related handlers."""

from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.types import ParseMode
from aiogram.utils.emoji import emojize

from recrierbot.domain import DomainRoot


def handler_tokens(dispatcher: Dispatcher, domain: DomainRoot):
    bot = dispatcher.bot

    @dispatcher.message_handler(commands=['newtoken'])
    async def handle_newtoken(message: Message):
        tokens_for_chat = await domain.repo.token.find_tokens(message.chat.id)

        if len(tokens_for_chat) > domain.settings.user_tokens_limit:
            await bot.send_message(
                message.chat.id,
                text=f'Limit of tokens of {domain.settings.user_tokens_limit} is exceeded. '
                     f'Use /listtokens to see all of your tokens.'
            )
            return

        new_token = domain.factory.token.create()
        await domain.repo.token.add(message.chat.id, new_token)
        await bot.send_message(
            message.chat.id,
            text=f'Here\'s your new token: `{new_token}`',
            parse_mode=ParseMode.MARKDOWN
        )

    @dispatcher.message_handler(commands=['listtokens'])
    async def handle_listtokens(message: Message):
        tokens = await domain.repo.token.find_tokens(message.chat.id)
        if not tokens:
            text = 'No tokens are created.'
        else:
            text = '\n'.join((token for token in tokens))

        await bot.send_message(message.chat.id, text)

    @dispatcher.message_handler(commands=['deltoken'])
    async def handle_deltoken(message: Message):
        token_values_to_delete = message.get_args().split()
        if not token_values_to_delete:
            await bot.send_message(message.chat.id,
                                   'Give me tokens to delete: \n'
                                   '\\deltoken a1Bd3f 7ab1cd ...')
            return

        await domain.repo.token.delete(token_values_to_delete)
        await bot.send_message(message.chat.id, emojize('Done. :heavy_check_mark:'))
