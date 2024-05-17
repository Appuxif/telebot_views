from datetime import datetime
from logging import getLogger
from typing import Any, ClassVar, Type
from uuid import uuid4

from pydantic import BaseModel, Field
from telebot_models.models import BaseModelManager, Model, ModelConfig

from telebot_views.utils import now_utc

logger = getLogger(__name__)


class UserStateCb(ModelConfig, BaseModel):
    """User State Callback"""

    id: str = Field(default_factory=lambda: uuid4().hex)
    view_name: str = ''
    page_num: int | None = None
    created_at: datetime | None = Field(default_factory=now_utc)
    view_params: dict = Field(default_factory=dict)
    params: dict = Field(default_factory=dict)


class UserMainState(ModelConfig, BaseModel):
    """User Main State"""

    view_name: str = ''
    callbacks: dict[str, UserStateCb] = Field(default_factory=dict)
    messages_to_delete: list[tuple[int, int]] = Field(default_factory=list)
    created_at: datetime | None = Field(default_factory=now_utc)

    def add_message_to_delete(self, chat_id: int, message_id: int):
        self.messages_to_delete.append((chat_id, message_id))


class UserModel(Model):
    """User Model"""

    user_id: int = 0
    username: str = ''
    first_name: str = ''
    last_name: str = ''
    state: UserMainState = Field(default_factory=UserMainState)
    keyboard_id: int | None = None
    constants: dict[str, Any] = Field(default_factory=dict)
    is_superuser: bool = False

    manager: ClassVar[Type['UserModelManager']]


class UserModelManager(BaseModelManager[UserModel]):
    """User Model Manager"""

    collection = 'users'
    model = UserModel


class State:
    user_model: Type[UserModel] = UserModel


def get_user_model() -> Type[UserModel]:
    return State.user_model


def set_user_model(model: Type[UserModel]) -> None:
    State.user_model = model


async def init_users_collection() -> None:
    logger.info('Init users collection...')
    collection = UserModelManager.get_collection()
    await collection.create_index('user_id', unique=True, background=True)
    logger.info('Init users collection done')
