# -*- coding: utf-8 -*-

import os
import json
import random
import string
import asyncio
import logging
import collections
import multiprocessing.pool

import sqlalchemy as sa
from sqlalchemy.engine.url import URL as DatabaseURL

import telegram
import telegram.ext
from telegram.ext.filters import Filters

import tornado.web
import tornado.ioloop

import emoji


BOT_URL = os.environ['BOT_URL'].rstrip('/') + '/'
TOKEN = os.environ['TELEGRAM_TOKEN']

CHAT_TOKENS_LIMIT = int(os.environ.get('CHAT_TOKENS_LIMIT', 7))

DB_PATH = os.environ.get('DB_PATH', '/var/lib/recrierbot/db.sqlite3')
THREADS_NUMBER = int(os.environ.get('THREADS_NUMBER', 4))
TORNADO_PORT = int(os.environ.get('TORNADO_PORT', 8080))


LOGLEVEL = os.environ.get('LOGGING_LEVEL', 'WARNING')
if LOGLEVEL.isnumeric():
    LOGLEVEL = int(LOGLEVEL)
else:
    try:
        LOGLEVEL = getattr(logging, LOGLEVEL)
    except Exception:
        logging.exception(f'No such logging level: {LOGLEVEL}. Using default: WARNING')
        LOGLEVEL = logging.WARNING

logging.getLogger().setLevel(LOGLEVEL)
logging.getLogger('tornado.access').setLevel(LOGLEVEL)
logging.getLogger('tornado.general').setLevel(LOGLEVEL)
logging.getLogger('tornado.application').setLevel(LOGLEVEL)


# = = = = =

db_url = DatabaseURL('sqlite', database=DB_PATH)
db_engine = sa.create_engine(db_url)
meta = sa.MetaData(bind=db_engine)

chat_token_t = sa.Table(
    'chattoken', meta,

    sa.Column('chat_id', sa.BIGINT),
    sa.Column('token', sa.CHAR(32)),

    sa.PrimaryKeyConstraint('chat_id', 'token'),
    sa.Index('chattoken_token', 'token', unique=True),
)


if not os.path.isfile(DB_PATH):
    open(DB_PATH, 'w').close()

meta.create_all(checkfirst=True)


class ChatTokenRepository:

    _chat_id_to_tokens = collections.defaultdict(lambda: [])
    """:type: dict[int, list[str]]"""

    _token_to_chat_id = {}
    """:type: dict[str, int]"""

    @classmethod
    def get_tokens_by_chat_id(cls, chat_id):
        if chat_id in cls._chat_id_to_tokens:
            return cls._chat_id_to_tokens[chat_id]

        tokens = [
            row.token
            for row in sa.select([chat_token_t.c.token]).where(chat_token_t.c.chat_id == chat_id).execute().fetchall()
        ]

        cls._chat_id_to_tokens[chat_id] = tokens
        return tokens

    @classmethod
    def get_chat_id_by_token(cls, token):
        if token in cls._token_to_chat_id:
            return cls._token_to_chat_id[token]
        chat_id = sa.select([chat_token_t.c.chat_id]).where(chat_token_t.c.token == token).scalar()
        cls._token_to_chat_id[token] = chat_id
        return chat_id

    @classmethod
    def save_token_for_chat_id(cls, chat_id, token):
        token_exists = chat_token_t.bind.scalar(sa.select([
            sa.exists([
                chat_token_t.select().where(sa.and_(chat_token_t.c.token == token)).limit(1)
            ])
        ]))

        if token_exists:
            return False

        chat_token_t.insert().values({'chat_id': chat_id, 'token': token}).execute()
        cls._chat_id_to_tokens[chat_id].append(token)
        cls._token_to_chat_id[token] = chat_id
        return True

    @classmethod
    def delete_tokens(cls, tokens, chat_id):
        query = chat_token_t.delete().where(chat_token_t.c.token.in_(tokens))
        if chat_id:
            query = query.where(chat_token_t.c.chat_id == chat_id)
        rowcount = query.execute().rowcount
        if rowcount:
            cls._chat_id_to_tokens.pop(chat_id, None)
            for token in tokens:
                cls._token_to_chat_id.pop(token, None)
            return rowcount
        else:
            return False


# = = = = =


def generate_token():
    token = _generate_token()
    while token == globals().get('HOOK_TOKEN'):
        token = _generate_token()
    return token


def _generate_token():
    smpl = string.digits + string.ascii_letters
    token = ''.join(random.sample(smpl, 32))
    return token


HOOK_TOKEN = generate_token()


# = = = = =


bot = telegram.Bot(TOKEN)
bot_dispatcher = telegram.ext.Dispatcher(bot, None, workers=0)


def filter_by_chat_type(chat_types):
    """
    :param list[str] chat_types:
    :rtype: telegram.ext.BaseFilter
    """
    return type('FilterBy{}Chat'.format('And'.join([chat_type.title() for chat_type in chat_types])),
                (telegram.ext.BaseFilter,),
                {'filter': lambda message: message.chat.type in chat_types})()


def command_handler(cmd_name, **kwargs):
    def outer(fn):
        filters = (
            Filters.entity(telegram.MessageEntity.MENTION) | filter_by_chat_type([telegram.Chat.PRIVATE])
        )

        for passed_filter in kwargs.pop('filters', []):
            filters &= passed_filter

        handler = telegram.ext.CommandHandler(cmd_name, fn, filters=filters, **kwargs)
        bot_dispatcher.add_handler(handler)
        return fn
    return outer


def message_handler(fn):
    filters = (
        Filters.text
        & (Filters.entity(telegram.MessageEntity.MENTION) | (filter_by_chat_type([telegram.Chat.PRIVATE])))
    )
    handler = telegram.ext.MessageHandler(filters, fn)
    bot_dispatcher.add_handler(handler)
    return fn


@command_handler('start')
def cmd_start(bot, update):
    """

    :param telegram.Bot bot:
    :param telegram.Update update:
    """
    bot.send_message(update.effective_chat.id, 'Hi. Use /newtoken to generate a new token.')


@command_handler('newtoken')
def cmd_newtoken(bot, update):
    """

    :param telegram.Bot bot:
    :param telegram.Update update:
    """

    tokens_for_chat_id = ChatTokenRepository.get_tokens_by_chat_id(update.effective_chat.id)
    if len(tokens_for_chat_id) > CHAT_TOKENS_LIMIT:
        bot.send_message(update.effective_chat.id, f'Limit of tokens of {CHAT_TOKENS_LIMIT} is exceeded. Use /listtokens to see all of your tokens.')
        return
    while True:
        new_token = generate_token()
        if ChatTokenRepository.save_token_for_chat_id(update.effective_chat.id, new_token):
            break
    bot.send_message(update.effective_chat.id, new_token)


@command_handler('listtokens')
def cmd_listtokens(bot, update):
    """

    :param telegram.Bot bot:
    :param telegram.Update update:
    """
    tokens = ChatTokenRepository.get_tokens_by_chat_id(update.effective_chat.id)
    bot.send_message(update.effective_chat.id, '\n'.join(tokens) or 'No tokens are created.')


@command_handler('ping')
def cmd_ping(bot, update):
    """

    :param telegram.Bot bot:
    :param telegram.Update update:
    """
    bot.send_message(update.effective_chat.id, emoji.emojize('Pong :wink:', use_aliases=True))


@command_handler('deltoken')
def cmd_deltoken(bot, update, args=None):
    """

    :param telegram.Bot bot:
    :param telegram.Update update:
    :param list[str] args:
    """
    if not args:
        bot.send_message(update.effective_chat.id, 'Give me tokens to delete.')
        return
    tokens = args
    message = update.effective_message  # type: telegram.Message
    ChatTokenRepository.delete_tokens(tokens, update.effective_chat.id)
    bot.send_message(update.effective_chat.id, emoji.emojize('Done. :heavy_check_mark:', use_aliases=True))


@message_handler
def msg_hahndler(bot, update):
    """

    :param telegram.Bot bot:
    :param telegram.Update update:
    """
    bot.send_message(update.effective_chat.id, emoji.emojize('What? :sweat_smile:', use_aliases=True))


# = = = = =


pool = multiprocessing.pool.ThreadPool(THREADS_NUMBER)


def in_thread(fn):

    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        future = asyncio.Future()
        pool.apply_async(fn, args=args, kwds=kwargs,
                         callback=lambda result: loop.call_soon_threadsafe(lambda: future.set_result(result)),
                         error_callback=lambda err: loop.call_soon_threadsafe(lambda: future.set_exception(err)))
        return await future

    return wrapper


class MessageHandler(tornado.web.RequestHandler):

    @in_thread
    def get(self, token=None):
        mode = self.get_argument('mode', None)
        message = self.get_argument('message')
        self.process_request({'token': token, 'message': message, 'mode': mode})

    @in_thread
    def post(self, token):
        data = json.loads(self.request.body)
        data['token'] = token
        self.process_request(data)

    def process_request(self, data):
        token = data.get('token')
        if not token:
            self.set_status(400)
            self.write(json.dumps({'result': 'error', 'description': 'user is none'}))
            return

        mode = data.get('mode')
        message = data['message']

        if not message:
            self.set_status(400)
            self.write(json.dumps({'result': 'error', 'description': 'the Message is empty'}))
            return

        chat_id = ChatTokenRepository.get_chat_id_by_token(token)
        if not chat_id:
            self.set_status(400)
            self.write(json.dumps({'result': 'error', 'description': 'user is unknown'}))
            return

        if not mode:
            mode = False
        elif not mode or mode.lower() not in ['markdown', 'html']:
            self.set_status(400)
            self.write(json.dumps({'result': 'error', 'description': 'parse mode is unknown'}))
            return

        try:
            bot.send_message(chat_id, message, parse_mode=mode)
            self.write(json.dumps({'result': 'ok'}))
        except Exception:
            self.write(json.dumps({'result': 'error', 'description': 'could not send message to telegram'}))


class TelegramHookHandler(tornado.web.RequestHandler):

    @in_thread
    def post(self):
        update = telegram.Update.de_json(json.loads(self.request.body), bot)
        bot_dispatcher.process_update(update)


class StatusHandler(tornado.web.RequestHandler):

    def get(self):
        webhook_is_set_str = 'is set' if status_webhook_is_set else 'is not set'
        self.write('Server is ok.\n'
                   f'Webhook {webhook_is_set_str}\n')


# = = = = =


class run_until_no_err:

    def __init__(self, fn, err_callback=None):
        self.fn = fn
        self.err_callback = err_callback

    def on_error(self, err_callback):
        self.err_callback = err_callback

    def __call__(self, *args, **kwargs):
        cnt = 0
        while True:
            try:
                cnt += 1
                self.fn(*args, **kwargs)
                break
            except Exception as err:
                err_cb_result = self.err_callback(err, cnt, *args, **kwargs)
                if err_cb_result == 'stop':
                    break
                elif err_cb_result == 'raise':
                    raise err
                continue


status_webhook_is_set = False


@run_until_no_err
def delete_and_set_webhook():
    global status_webhook_is_set
    bot.delete_webhook()
    logging.info(f'Setting webhook to {BOT_URL}{HOOK_TOKEN}/hook')
    bot.set_webhook(f'{BOT_URL}{HOOK_TOKEN}/hook')
    status_webhook_is_set = True


@delete_and_set_webhook.on_error
def _(err, cnt):
    logging.warning(f'Failed to set webhook. Retrying')


def main():
    app = tornado.web.Application([
        (r'/(?P<token>.*?)/send', MessageHandler),
        (rf'/{HOOK_TOKEN}/hook', TelegramHookHandler),
        (rf'/status', StatusHandler)
    ])

    app.listen(TORNADO_PORT)

    asyncio.get_event_loop().call_later(5, delete_and_set_webhook)
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
