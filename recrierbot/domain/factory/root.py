from .token import TokenFactory


class FactoryRoot(object):
    token: TokenFactory

    def __init__(self):
        self.token = TokenFactory()
