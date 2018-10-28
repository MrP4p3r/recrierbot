from aiogram.types import Message
from aiogram.dispatcher.filters import Filter


class UnknownCommand(Filter):

    # FIXME: hardcode...
    known_commands = ['start', 'newtoken', 'deltoken', 'listtokens', 'ping']

    def check(self, obj):
        return bool(isinstance(obj, Message)
                    and obj.is_command()
                    and obj.get_command(pure=True) not in self.known_commands)

