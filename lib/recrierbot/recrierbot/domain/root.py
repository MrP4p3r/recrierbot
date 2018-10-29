from recrierbot.settings import DomainSettings
from .tokens import Tokens


class DomainRoot(object):

    settings: DomainSettings
    tokens: Tokens

    def __init__(self, connection_getter, settings: DomainSettings):
        self.settings = settings
        self.tokens = Tokens(connection_getter)
