from telebot.types import InlineKeyboardButton

from telebot_views.base import BaseMessageSender, BaseView, RouteResolver
from telebot_views.services.subscriptions import ensure_subscription


class MainRouteResolver(RouteResolver):
    """Main Route Resolver"""

    view: "MainView"

    async def resolve(self) -> bool:
        if self.view.ensure_subscription_chat_id:
            user = await self.request.get_user()
            subscribed = await ensure_subscription(
                self.view.ensure_subscription_chat_id,
                user.user_id,
            )
            if not subscribed:
                return True

        return self.request.message.text == '/start' or await super().resolve()


class MainMessageSender(BaseMessageSender):
    """Main Message Sender"""

    async def get_keyboard(self) -> list[list[InlineKeyboardButton]]:
        # cb = UserStateCb
        r = self.view.route_resolver.routes_registry
        return [
            [await self.view.buttons.view_btn(r['CHECK_SUB_VIEW'], 1)],
        ]

    async def get_keyboard_text(self) -> str:
        return self.view.labels[0]


class MainView(BaseView):
    """Отображение главного меню"""

    view_name = 'MAIN_VIEW'
    edit_keyboard = False
    labels = [
        'Главное меню',
        'В главное меню',
    ]

    route_resolver = MainRouteResolver
    message_sender = MainMessageSender

    ensure_subscription_chat_id: int = 0
