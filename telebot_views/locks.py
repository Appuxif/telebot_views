import asyncio
from datetime import timedelta
from logging import getLogger
from typing import Optional
from uuid import uuid4

from pymongo import ReturnDocument
from telebot_models.models import CollectionGetter

from telebot_views.utils import now_utc

COLL_NAME = 'telebot_views_locks'
logger = getLogger(__name__)


class Lock:
    _task: Optional[asyncio.Task] = None

    def __init__(self, lock_key: str, lock_ttl: int, wait: bool = True, reacquire: bool = True) -> None:
        self._lock_key = lock_key
        self._lock_ttl = lock_ttl
        self._collection = CollectionGetter.get_collection(COLL_NAME)
        self._lock_id = uuid4()
        self._async_lock = asyncio.Lock()
        self._wait = wait
        self._reacquire = reacquire

    def locked(self) -> bool:
        return self._async_lock.locked()

    async def acquire(self) -> bool:
        logger.debug('Acquiring Lock `%s`...', self._lock_key)
        if self.locked():
            raise AlreadyLocked

        logger.debug('Acquiring async Lock `%s`...', self._lock_key)
        await self._async_lock.acquire()
        logger.debug('Async Lock `%s` acquired', self._lock_key)

        last_log = asyncio.get_running_loop().time()
        while True:
            now = now_utc()
            await self._collection.update_one({'key': self._lock_key}, {'$set': {'key': self._lock_key}}, upsert=True)
            doc = await self._collection.find_one_and_update(
                {
                    'key': self._lock_key,
                    '$or': [
                        {'acquired_at': None},
                        {'acquired_at': {'$lt': now - timedelta(seconds=self._lock_ttl)}},
                    ],
                },
                {'$set': {'key': self._lock_key, 'lock_id': str(self._lock_id), 'acquired_at': now}},
                return_document=ReturnDocument.AFTER,
            )
            result = doc is not None
            if result or not result and not self._wait:
                break

            if asyncio.get_running_loop().time() - last_log > 5:
                logger.debug('Lock `%s` was not acquired. Waiting...', self._lock_key)
                last_log = asyncio.get_running_loop().time()

            await asyncio.sleep(0.5)

        if result is True:
            logger.debug('Lock `%s` was acquired', self._lock_key)
            if self._reacquire:
                self._task = asyncio.create_task(self._reacquire_task())
        else:
            logger.debug('Lock `%s` was not acquired', self._lock_key)
        return result

    async def reacquire(self) -> bool:
        if not self.locked():
            logger.debug('Cannot reacquire Lock `%s`', self._lock_key)
            return False

        doc = await self._collection.find_one_and_update(
            {'lock_id': str(self._lock_id), 'key': self._lock_key},
            {'$set': {'acquired_at': now_utc()}},
            return_document=ReturnDocument.AFTER,
        )
        result = doc is not None
        if result:
            logger.debug('Lock `%s` was reacquired', self._lock_key)
        else:
            logger.debug('Lock `%s` was not reacquired\n%s', self._lock_key, doc)
        return result

    async def release(self) -> None:
        logger.debug('Releasing Lock `%s`...', self._lock_key)
        if self.locked():
            doc = await self._collection.find_one_and_delete(
                {'lock_id': str(self._lock_id), 'key': self._lock_key},
            )
            if not doc:
                logger.debug('Doc for Lock `%s` was not deleted\n%s', self._lock_key, doc)
            self._async_lock.release()
            logger.debug('Async Lock `%s` was released', self._lock_key)
            if self._task:
                await self._task
        logger.debug('Lock `%s` was released', self._lock_key)

    async def _reacquire_task(self) -> None:
        threshold = max(0.3, self._lock_ttl - int(self._lock_ttl / 2))
        last_try = asyncio.get_running_loop().time()
        logger.debug('Reacquiring task for Lock `%s` started every %s', self._lock_key, threshold)
        while self.locked():
            await asyncio.sleep(0.05)
            if asyncio.get_running_loop().time() - last_try > threshold:
                last_try = asyncio.get_running_loop().time()
                if not await self.reacquire():
                    break
        logger.debug('Reacquiring task for Lock `%s` cancelled', self._lock_key)

    async def __aenter__(self) -> None:
        await self.acquire()
        return None

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.release()


class AlreadyLocked(Exception):
    pass


async def init_locks_collection() -> None:
    logger.info('Init locks collection...')
    collection = CollectionGetter.get_collection(COLL_NAME)
    await collection.create_index('key', unique=True, background=True)
    await collection.create_index('lock_id', background=True)
    await collection.create_index('acquired_at', background=True, expireAfterSeconds=3600 * 24)
    logger.info('Init locks collection done')
