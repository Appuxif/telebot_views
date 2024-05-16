from logging import getLogger
from typing import ClassVar, Type

from pymongo import ReturnDocument
from telebot_models.models import BaseModelManager, Model

from telebot_views import bot
from telebot_views.models.users import UserStateCb

logger = getLogger(__name__)


class LinkModel(Model):
    """Link"""

    callback: UserStateCb

    manager: ClassVar[Type['LinkModelManager']]

    def get_bot_start_link(self) -> str:
        return f't.me/{bot.bot.user.username}?start=link_{self.id}'


class LinkModelManager(BaseModelManager[LinkModel]):
    """Links Model Manager"""

    collection = 'links'
    model = LinkModel

    async def get_or_create(self, model: LinkModel) -> LinkModel:
        exclude = {'id': True, 'callback': {'id': True, 'created_at': True}}
        obj = model.dict(by_alias=True, exclude=exclude)
        logger.debug(
            'Creating link:\nexclude=%s\nobj=%s',
            exclude,
            obj,
        )
        document = await self.get_collection().find_one_and_update(
            obj,
            {'$set': obj},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return self.model.parse_obj(document)


async def init_links_collection() -> None:
    logger.info('Init links collection...')
    collection = LinkModelManager.get_collection()
    await collection.create_index('callback.id', background=True)
    await collection.create_index('callback.view_name', background=True)
    logger.info('Init links collection done')
