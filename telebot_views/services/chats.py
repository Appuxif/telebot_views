from datetime import timedelta

from asyncio_functools import async_lru_cache
from telebot import asyncio_helper
from telebot.types import Chat

from telebot_views import bot
from telebot_views.models.cache import CacheModel
from telebot_views.utils import now_utc


@async_lru_cache(100)
async def get_chat(chat_id: int) -> Chat:
    cache_key = f'get_chat:{chat_id}'
    cache = await CacheModel.manager().by_key(cache_key).is_valid().find_one(raise_exception=False)

    if cache is None:
        chat_dict = await asyncio_helper.get_chat(bot.bot.token, chat_id)

        cache = CacheModel(
            key=cache_key,
            data=chat_dict,
            valid_until=now_utc() + timedelta(minutes=5),
        )
        await cache.insert()

    return Chat.de_json(cache.data)
