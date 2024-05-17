from datetime import datetime, timedelta
from logging import getLogger
from typing import Any, Callable, ClassVar, Type

from pydantic import Field
from telebot_models.models import BaseModelManager, Model

from telebot_views.utils import now_utc

logger = getLogger(__name__)


class CacheModel(Model):
    """Cache Model"""

    key: str
    data: dict = Field(default_factory=dict)
    valid_until: datetime | None = None

    manager: ClassVar[Type['CacheModelManager']]


class CacheModelManager(BaseModelManager[CacheModel]):
    """Cache Model Manager"""

    collection = 'caches'
    model: Type[CacheModel] = CacheModel

    def by_key(self, key: str) -> 'CacheModelManager':
        return self.filter({'key': key})

    def is_valid(self) -> 'CacheModelManager':
        return self.filter({'valid_until': {'$gt': now_utc()}})


def with_cache(
    cache_key: str,
    cache_ttl: int,
    serializer: Callable[[Any], dict] = lambda x: x,
    deserializer: Callable[[dict], Any] = lambda x: x,
    force: bool = False,
):
    def decorator(func):
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache = await CacheModel.manager().by_key(cache_key).is_valid().find_one(raise_exception=False)

            if cache is not None:
                logger.debug('Got cache for key `%s`', cache_key)
                if not force:
                    return deserializer(cache.data)
            else:
                logger.debug('Cache for key `%s` not found', cache_key)

            result = await func(*args, **kwargs)

            valid_until = now_utc() + timedelta(seconds=cache_ttl)

            if cache is not None and force:
                logger.debug('Forcing cache renew for `%s`', cache_key)
                cache.data = serializer(result)
                cache.valid_until = valid_until
                await cache.update(include={'data', 'valid_until'})

            if cache is not None and not force:
                raise ValueError('Unknown behaviour')

            await CacheModel(
                key=cache_key,
                data=serializer(result),
                valid_until=valid_until,
            ).insert()

            return result

        return wrapper

    return decorator


async def init_caches_collection() -> None:
    logger.info('Init caches collection...')
    collection = CacheModelManager.get_collection()
    await collection.create_index('key', background=True)
    await collection.create_index('valid_until', expireAfterSeconds=3600 * 24 * 30, background=True)
    logger.info('Init caches collection done')
