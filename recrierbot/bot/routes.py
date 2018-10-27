"""Registers all handlers via dispatcher."""

from aiogram import Dispatcher
from recrierbot.domain import DomainRoot
from .handlers import *


def check_in(dispatcher: Dispatcher, domain: DomainRoot):
    handler_start(dispatcher)
    handler_generic(dispatcher)
    handler_tokens(dispatcher, domain)
