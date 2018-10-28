from aiogram.types import Message
from aiogram.dispatcher.filters import Filter


class NotCommandFilter(Filter):

    def check(self, obj):
        return bool(isinstance(obj, Message) and not obj.is_command())
