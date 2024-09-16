import asyncio
from contextlib import suppress
from dataclasses import dataclass
from logging import getLogger
from typing import Any, Optional, Union

from telebot.async_telebot import AsyncTeleBot
from telebot.types import BusinessConnection, CallbackQuery, InlineQuery, Message

from telebot_views import bot
from telebot_views.base import Request, Route, RouteResolver
from telebot_views.dispatcher import ViewDispatcher
from telebot_views.dummy import DummyView
from telebot_views.locks import Lock, init_locks_collection
from telebot_views.models.cache import init_caches_collection, with_cache
from telebot_views.models.links import init_links_collection
from telebot_views.models.users import init_users_collection

logger = getLogger('telebot_views')


def set_bot(tele_bot: AsyncTeleBot):
    bot.bot = tele_bot


def set_reports_bot(tele_bot: AsyncTeleBot, reports_chat_id: Union[str, int]):
    bot.reports_bot = tele_bot
    bot.reports_chat_id = reports_chat_id


def init(
    tele_bot: AsyncTeleBot,
    routes: list[Route],
    skip_non_private: bool = False,
    reports_bot: Optional[AsyncTeleBot] = bot.reports_bot,
    reports_chat_id: Union[str, int] = bot.reports_chat_id,
    loop: Optional[asyncio.BaseEventLoop] = None,
    business_connection_id: Optional[int] = None,
):
    # pylint: disable=too-many-arguments
    set_bot(tele_bot)
    set_reports_bot(reports_bot, reports_chat_id)

    for route in routes + [Route(DummyView)]:
        RouteResolver.register_route(route)

    async def message_handler(msg: Message):
        nonlocal skip_non_private, business_connection_id
        try:
            if skip_non_private and msg.chat.type != 'private':
                return

            if msg.business_connection_id and msg.business_connection_id != business_connection_id:
                con = await _get_business_connection(msg.business_connection_id)
                logger.warning(
                    'Unknown business_connection_id: %s\nuser_chat_id=%s\n%s',
                    msg.business_connection_id,
                    con['user_chat_id'],
                    con,
                )
                return

            if msg.from_user.id == tele_bot.token.split(':', 1)[0]:
                return

            request = Request(msg=msg)
            async with Lock(f'user:{msg.from_user.id}', 30):
                await ViewDispatcher(request=request).dispatch()
        except Exception:
            logger.exception(
                'message_handler error\nuser_id: %s\nusername: %s\nfirst_name: %s\nlast_name: %s',
                msg.from_user.id,
                msg.from_user.username,
                msg.from_user.first_name,
                msg.from_user.last_name,
            )
            await bot.bot_answer_message(msg, 'Что-то пошло не так. Попробуйте еще раз или введите /start')
            raise

    tele_bot.message_handler()(message_handler)
    tele_bot.business_message_handler()(message_handler)

    @tele_bot.callback_query_handler(func=lambda call: True)
    async def callback_query(callback: CallbackQuery):
        nonlocal skip_non_private
        try:
            if skip_non_private and callback.message.chat.type != 'private':
                return

            request = Request(callback=callback)
            async with Lock(f'user:{callback.from_user.id}', 30):
                await ViewDispatcher(request=request).dispatch()
        except Exception:
            logger.exception(
                'callback_query error\nuser_id: %s\nusername: %s\nfirst_name: %s\nlast_name: %s',
                callback.from_user.id,
                callback.from_user.username,
                callback.from_user.first_name,
                callback.from_user.last_name,
            )
            with suppress(Exception):
                await bot.bot.answer_callback_query(
                    callback.id,
                    'Что-то пошло не так. Попробуйте еще раз или введите /start',
                    show_alert=True,
                )
            raise

    @tele_bot.inline_handler(lambda x: True)
    async def inline_query(inline: InlineQuery):
        nonlocal skip_non_private
        try:
            if skip_non_private and inline.chat_type != 'sender':
                return

            request = Request(inline=inline)
            async with Lock(f'user:{inline.from_user.id}', 30):
                await ViewDispatcher(request=request).dispatch()
        except Exception:
            logger.exception(
                'inline_query error\nuser_id: %s\nusername: %s\nfirst_name: %s\nlast_name: %s',
                inline.from_user.id,
                inline.from_user.username,
                inline.from_user.first_name,
                inline.from_user.last_name,
            )
            raise

    if not loop:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.create_task(init_users_collection())
    loop.create_task(init_caches_collection())
    loop.create_task(init_links_collection())
    loop.create_task(init_locks_collection())


async def _get_business_connection(business_connection_id: str) -> dict[str, Any]:
    @with_cache(f'get_business_connection:{business_connection_id}', 3600)
    async def inner() -> dict[str, Any]:
        obj = await bot.bot.get_business_connection(business_connection_id)
        return {
            'user_chat_id': obj.user_chat_id,
            'user_id': obj.user.id,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'username': obj.user.username,
        }

    return await inner()
