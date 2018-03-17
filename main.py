# -*- coding: utf-8 -*-

import os
import json
import random
import string
import asyncio
import multiprocessing.pool

import telegram
import telegram.ext

import sqlalchemy as sa
from sqlalchemy.engine.url import URL as DatabaseURL

import tornado.web
import tornado.ioloop


BOT_URL = os.environ['BOT_URL'].rstrip('/') + '/'
TOKEN = os.environ['TELEGRAM_TOKEN']

CHAT_TOKENS_LIMIT = os.environ.get('CHAT_TOKENS_LIMIT', 7)

DB_PATH = os.environ.get('DB_PATH', '/var/lib/recrierbot/db.sqlite3')
THREADS_NUMBER = int(os.environ.get('THREADS_NUMBER', 4))
TORNADO_PORT = int(os.environ.get('TORNADO_PORT', 8080))


# = = = = =

db_url = DatabaseURL('sqlite', database='/var/lib/qeq.db')
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

    @staticmethod
    def get_tokens_by_chat_id(chat_id):
        tokens = [
            row.token
            for row in sa.select([chat_token_t.c.token]).where(chat_token_t.c.chat_id == chat_id).execute().fetchall()
        ]
        return tokens

    @staticmethod
    def get_chat_id_by_token(token):
        return sa.select([chat_token_t.c.chat_id]).where(chat_token_t.c.token == token).scalar()

    @staticmethod
    def save_token_for_chat_id(chat_id, token):
        token_exists = sa.select([
            sa.exists([
                chat_token_t.select().where(sa.and_(chat_token_t.c.token == token)).limit(1)
            ])
        ]).scalar()

        if token_exists:
            return False

        chat_token_t.insert().values({'chat_id': chat_id, 'token': token}).execute()
        return True

    @staticmethod
    def delete_tokens(tokens, chat_id):
        query = chat_token_t.delete.where(chat_token_t.c.token.in_(tokens))
        if chat_id:
            query = query.where(chat_token_t.c.chat_id == chat_id)
        return query.execute().rowcount


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


def command_handler(cmd_name, **kwargs):
    def outer(fn):
        handler = telegram.ext.CommandHandler(cmd_name, fn, **kwargs)
        bot_dispatcher.add_handler(handler)
        return fn
    return outer


def message_handler(fn):
    handler = telegram.ext.MessageHandler(None, fn)
    bot_dispatcher.add_handler(handler)
    return fn


@message_handler
def msg_hahndler(bot, update):
    """

    :param telegram.Bot bot:
    :param telegram.Update update:
    """
    bot.send_message(update.effective_chat.id, 'What? :sweat_smile:')


@command_handler('start')
def cmd_start(bot, update):
    """

    :param telegram.Bot bot:
    :param telegram.Update update:
    """
    bot.send_message('Hi. Use /newtoken to generate a new token.')


@command_handler('newtoken')
def cmd_start(bot, update):
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
    bot.send_message(update.effective_chat.id, '\n'.join(tokens))


@command_handler('ping')
def cmd_ping(bot, update):
    """

    :param telegram.Bot bot:
    :param telegram.Update update:
    """
    bot.send_message(update.effective_chat.id, 'Pong :wink:')


@command_handler('deltoken', pass_args=True)
def cmd_deltoken(bot, update, tokens):
    """

    :param telegram.Bot bot:
    :param telegram.Update update:
    :param list[str] tokens:
    """
    message = update.effective_message  # type: telegram.Message
    ChatTokenRepository.delete_tokens(tokens, update.effective_chat.id)
    bot.send_message(update.effective_chat.id, 'Done. :heavy_check_mark:')


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
        mode = self.get_argument('mode')
        message = self.get_argument('message')
        self.process_request({'token': token, 'message': message, 'mode': mode})

    @in_thread
    def post(self):
        data = json.loads(self.request.body)
        self.process_request(data)

    def process_request(self, data):
        token = data.get('token')
        if not token:
            self.set_status(400)
            self.write(json.dumps({'result': 'error', 'description': 'user is none'}))
            return

        mode = data.get('mode')
        message = data.get('message')

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


def main():
    app = tornado.web.Application([
        (r'/(?P<token>.*?)/send', MessageHandler),
        (rf'/{HOOK_TOKEN}/hook', TelegramHookHandler),
    ])

    app.listen(TORNADO_PORT)

    bot.delete_webhook()
    bot.set_webhook(BOT_URL + f'/{HOOK_TOKEN}/hook')

    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
