import asyncio
from contextlib import suppress
from logging import getLogger
from typing import Optional, Union

from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery, Message

from telebot_views import bot
from telebot_views.base import Request, Route, RouteResolver
from telebot_views.dispatcher import ViewDispatcher
from telebot_views.dummy import DummyView
from telebot_views.locks import init_locks_collection
from telebot_views.models.cache import init_caches_collection
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
):
    set_bot(tele_bot)
    set_reports_bot(reports_bot, reports_chat_id)

    for route in routes + [Route(DummyView)]:
        RouteResolver.register_route(route)

    @tele_bot.message_handler()
    async def message_handler(msg: Message):
        nonlocal skip_non_private
        try:
            if skip_non_private and msg.chat.type != 'private':
                return
            if msg.from_user.id == tele_bot.token.split(':', 1)[0]:
                return

            request = Request(msg=msg)
            await ViewDispatcher(request=request).dispatch()
        except Exception:
            logger.exception(
                'message_handler error\nuser_id: %s\nusername: %s\nfirst_name: %s\nlast_name: %s',
                msg.from_user.id,
                msg.from_user.username,
                msg.from_user.first_name,
                msg.from_user.last_name,
            )
            await bot.bot.send_message(msg.chat.id, 'Что-то пошло не так. Попробуйте еще раз или введите /start')
            raise

    @tele_bot.callback_query_handler(func=lambda call: True)
    async def callback_query(callback: CallbackQuery):
        nonlocal skip_non_private
        try:
            if skip_non_private and callback.message.chat.type != 'private':
                return

            request = Request(callback=callback)
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

    if not loop:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.create_task(init_users_collection())
    loop.create_task(init_caches_collection())
    loop.create_task(init_links_collection())
    loop.create_task(init_locks_collection())
