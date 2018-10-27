"""Settings root."""

import os
import logging


class Settings(object):

    def __init__(self):
        self.db = DbSettings()
        self.web = WebServerSettings()
        self.bot = BotSettings()
        self.domain = DomainSettings()


class DbSettings(object):

    def __init__(self):
        self.type = 'sqlite3'
        self.path = os.environ.get('DB_PATH', '/var/lib/recrierbot/db.sqlite3')


class WebServerSettings(object):

    _DEFAULT_BIND = '0.0.0.0'
    _DEFAULT_PORT = 8080

    def __init__(self):
        if os.environ.get('THREADS_NUMBER'):
            logging.warning('THREADS_NUMBER variable is deprecated. We don\'t use threads anymore')

        if os.environ.get('TORNADO_PORT'):
            logging.warning('TORNADO_PORT variale is deprecated. Use HTTP_PORT.')

        self.bind = self._DEFAULT_BIND
        self.port = int(
            os.environ.get('HTTP_PORT')
            or os.environ.get('TORNADO_PORT')
            or self._DEFAULT_PORT
        )


class BotSettings(object):

    telegram_token: str
    base_bot_url: str
    socks5_proxy: str

    def __init__(self):
        self.telegram_token = os.environ['TELEGRAM_TOKEN']
        self.socks5_proxy = os.environ.get('SOCKS5_PROXY')

        if 'BOT_URL' in os.environ:
            self.base_bot_url = os.environ.get('BOT_URL').rstrip('/') + '/'
        else:
            self.base_bot_url = None


class DomainSettings(object):

    _DEFAULT_USER_TOKENS_LIMIT = 7

    def __init__(self):
        if os.environ.get('CHAT_TOKENS_LIMIT'):
            logging.warning('CHAT_TOKENS_LIMIT variable is deprecated. Use USER_TOKENS_LIMIT')
        self.user_tokens_limit = int(
            os.environ.get('USER_TOKENS_LIMIT')
            or os.environ.get('CHAT_TOKENS_LIMIT')
            or self._DEFAULT_USER_TOKENS_LIMIT
        )
