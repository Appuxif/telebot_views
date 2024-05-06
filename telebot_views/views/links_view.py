from typing import Optional

from telebot_models.models import PyObjectId

from telebot_views import RouteResolver
from telebot_views.base import BaseView
from telebot_views.dummy import DummyMessageSender
from telebot_views.models.links import LinkModel


class LinksRouteResolver(RouteResolver):
    """Route resolver to handle commands starting with /start link_<link_id>"""

    async def resolve(self) -> bool:
        link_id_is_valid = False
        if self.request.message.text.startswith('/start link_'):
            link_id = parse_link_id(self.request.message.text)
            link_id_is_valid = bool(link_id and PyObjectId.is_valid(link_id))
        return link_id_is_valid


class LinksView(BaseView):
    """Отображение для перенаправления ссылок через команду /start link_<link_id>"""

    view_name = 'LINKS_VIEW'
    message_sender = DummyMessageSender
    route_resolver = LinksRouteResolver
    labels = []

    async def redirect(self) -> Optional['BaseView']:
        link_id = PyObjectId(parse_link_id(self.request.message.text))
        link: Optional[LinkModel] = await LinkModel.manager().find_one(link_id, raise_exception=False)
        r = self.route_resolver.routes_registry
        if link is None or link.callback.view_name not in r:
            return None
        return r[link.callback.view_name].view(self.request, link.callback)


def parse_link_id(text: str) -> str:
    return text.split(' ')[1].split('_')[1]
