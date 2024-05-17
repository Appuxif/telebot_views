from typing import Optional

from telebot.types import InlineKeyboardButton

from telebot_views import bot
from telebot_views.base import BaseMessageSender, BaseView
from telebot_views.services.subscriptions import ensure_subscription


class CheckSubMessageSender(BaseMessageSender):
    """Check Sub Message Sender"""

    async def get_keyboard(self) -> list[list[InlineKeyboardButton]]:
        return []

    async def get_keyboard_text(self) -> str:
        return ''


class CheckSubView(BaseView):
    """Проверка подписки"""

    view_name = 'CHECK_SUB_VIEW'
    edit_keyboard = False
    labels = [
        'Проверка подписки на канал',
        'Проверить подписку на канал',
    ]

    message_sender = CheckSubMessageSender

    ensure_subscription_chat_id: int = 0

    async def redirect(self) -> Optional['BaseView']:
        r = self.route_resolver.routes_registry
        sub_result: bool = True
        if self.ensure_subscription_chat_id:
            user = await self.request.get_user()
            sub_result = await ensure_subscription(
                self.ensure_subscription_chat_id,
                user.user_id,
                force=True,
            )
        if sub_result:
            await bot.bot.send_message(self.request.message.chat.id, '✅ Подписка успешно проверена.')
        return r['MAIN_VIEW'].view(self.request, callback=self.callback, edit_keyboard=True)
