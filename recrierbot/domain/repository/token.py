"""Simpe token repository."""

import collections
from typing import Dict, List
import sqlalchemy as sa
from recrierbot.db import chat_token_t


class TokenRepository(object):
    """Not really a TOKEN repository. But worse is better, right?"""

    _chat_id_to_tokens: Dict[int, List[str]]
    _token_to_chat_id: Dict[str, int]

    def __init__(self, connection_getter):
        self._get_connection = connection_getter
        self._chat_id_to_tokens = collections.defaultdict(list)
        self._token_to_chat_id = {}

    async def add(self, chat_id: int, token: str):
        conn = await self._get_connection()
        await conn.execute(
            chat_token_t.insert().values({'chat_id': chat_id, 'token': token})
        )
        self._chat_id_to_tokens[chat_id].append(token)
        self._token_to_chat_id[token] = chat_id

    async def find_tokens(self, chat_id: int = None) -> List[str]:
        if chat_id in self._chat_id_to_tokens:
            return self._chat_id_to_tokens[chat_id]

        query = sa.select([chat_token_t.c.token]).where(chat_token_t.c.chat_id == chat_id)
        conn = await self._get_connection()
        result = await conn.execute(query)
        tokens = [row.token async for row in result]

        self._chat_id_to_tokens[chat_id] = tokens
        for token in tokens:
            self._token_to_chat_id[token] = chat_id

        return tokens

    async def find_chat_id(self, token: str = None) -> int:
        if token in self._token_to_chat_id:
            return self._token_to_chat_id[token]

        query = sa.select([chat_token_t.c.chat_id]).where(chat_token_t.c.token == token)
        conn = await self._get_connection()
        chat_id = await conn.scalar(query)

        self._token_to_chat_id[token] = chat_id
        self._chat_id_to_tokens[chat_id].append(token)
        return chat_id

    async def delete(self, tokens: List[str], chat_id: int = None):
        query = chat_token_t.delete().where(chat_token_t.c.token.in_(tokens))
        if chat_id is not None:
            query = query.where(chat_token_t.c.chat_id == chat_id)

        conn = await self._get_connection()
        result = await conn.execute(query)

        rowcount = result.rowcount

        if not rowcount:
            return

        if chat_id is not None:
            chat_ids = set((self._token_to_chat_id[token] for token in tokens if token in self._token_to_chat_id))
        else:
            chat_ids = {chat_id}

        for chat_id in chat_ids:
            self._chat_id_to_tokens[chat_id] = list(set(self._chat_id_to_tokens[chat_id]).difference(tokens))
        for token in tokens:
            self._token_to_chat_id.pop(token, None)

        return rowcount
