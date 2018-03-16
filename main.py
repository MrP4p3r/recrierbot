# -*- coding: utf-8 -*-

import os
import re
import json
import random
import string
import urllib.request
import urllib.parse
import logging
import asyncio
import multiprocessing.pool

import sqlalchemy as sa

import tornado.web
import tornado.ioloop


TOKEN = os.environ['TELEGRAM_TOKEN']
HOOK_TOKEN = os.environ['TELEGRAM_HOOK_TOKEN']
BASE_URL = f'https://api.telegram.org/bot{TOKEN}/'

CHAT_TOKENS_LIMIT = os.environ.get('CHAT_TOKENS_LIMIT', 7)

DB_PATH = os.environ.get('DB_PATH', '/var/lib/recrierbot/db.sqlite3')
THREADS_NUMBER = int(os.environ.get('THREADS_NUMBER', 4))
TORNADO_PORT = int(os.environ.get('TORNADO_PORT', 8080))


# = = = = =


db_engine = sa.create_engine(DB_PATH, pool_size=THREADS_NUMBER)
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
    while token == HOOK_TOKEN:
        token = _generate_token()
    return token


def _generate_token():
    smpl = string.digits + string.ascii_letters
    token = ''.join(random.sample(smpl, 32))
    return token


# = = = = =


def send_message_to_chat(chat_id, message):
    payload = {'chat_id': str(chat_id),
               'text': message,
               'disable_web_page_preview': 'true'}
    try:
        resp = urllib.request.urlopen(f'{BASE_URL}sendMessage', payload).read()
        return
    except Exception as err:
        logging.error(f'Could not send message to chat_id = {chat_id}')
        raise err


command_pattern = re.compile(fr'^(\/\w+)(?:@\w+bot)(?:\s+(.*)\s+$|$)')


def parse_bot_command(text):
    match = command_pattern.match(text)
    if match is None:
        return None, None
    return match.group(1), match.group(2)


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

        payload = {
            'chat_id': str(chat_id),
            'text': message,
            'disable_web_page_preview': 'true',
        }

        if mode:
            payload.update({'parse_mode': mode})

        try:
            _ = urllib.request.urlopen(BASE_URL + 'sendMessage', urllib.parse.urlencode(payload)).read()
            self.write(json.dumps({'result': 'ok'}))
        except Exception:
            self.write(json.dumps({'result': 'error', 'description': 'could not send message to telegram'}))


class TelegramHookHandler(tornado.web.RequestHandler):

    @in_thread
    def post(self):
        body = json.loads(self.request.body)

        update_id = body['update_id']
        message = body['message']

        message_id = message.get('message_id')
        date = message.get('date')
        text = message.get('text')
        from_ = message.get('from')

        chat = message['chat']
        chat_id = chat['id']
        chat_type = chat['type']

        if not text:
            return

        command, args = parse_bot_command(text)
        if command is None:
            send_message_to_chat(chat_id, 'Not a command.')
            return
        elif command == '/start':
            send_message_to_chat(chat_id, 'Hi. Use /newtoken to generate a new token.')
            return
        elif command == '/newtoken':
            tokens_for_chat_id = ChatTokenRepository.get_tokens_by_chat_id(chat_id)
            if len(tokens_for_chat_id) > CHAT_TOKENS_LIMIT:
                send_message_to_chat(chat_id, f'Limit of tokens of {CHAT_TOKENS_LIMIT} is exceeded. Use /listtokens to see all of your tokens.')
                return
            while True:
                new_token = generate_token()
                if ChatTokenRepository.save_token_for_chat_id(chat_id, new_token):
                    break
            send_message_to_chat(chat_id, new_token)
            return
        elif command == '/listtokens':
            tokens = ChatTokenRepository.get_tokens_by_chat_id(chat_id)
            send_message_to_chat(chat_id, '\n'.join(tokens))
            return
        elif command == '/ping':
            send_message_to_chat(chat_id, 'Pong :wink:')
            return
        elif command == '/deltoken':
            tokens = args.split()
            ChatTokenRepository.delete_tokens(tokens, chat_id)
            send_message_to_chat(chat_id, 'Done. :heavy_check_mark:')
            return
        else:
            send_message_to_chat(chat_id, 'What? :sweat_smile:')
            return


if __name__ == '__main__':
    app = tornado.web.Application([
        (r'/(?P<token>.*?)/send', MessageHandler),
        (rf'/{HOOK_TOKEN}/hook', TelegramHookHandler),
    ])

    server = app.listen(TORNADO_PORT)
    tornado.ioloop.IOLoop.instance()
