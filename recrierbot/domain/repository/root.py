from .token import TokenRepository


class RepositoryRoot(object):
    token: TokenRepository

    def __init__(self, connection_getter):
        self.token = TokenRepository(connection_getter)
