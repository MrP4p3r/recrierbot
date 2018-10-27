from recrierbot.settings import DomainSettings
from .repository import RepositoryRoot
from .factory import FactoryRoot


class DomainRoot(object):
    repo: RepositoryRoot
    factory: FactoryRoot
    settings: DomainSettings

    def __init__(self, connection_getter, settings: DomainSettings):
        self.repo = RepositoryRoot(connection_getter)
        self.factory = FactoryRoot()
        self.settings = settings
