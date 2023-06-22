from telebot_views.base import Request
from telebot_views.models import UserStateCb


class ViewDispatcher:
    """Диспетчер видов.
    По заданному запросу Request определяет, какой вид нужно выбрать
    для передачи запроса и отработки реакции на действие пользователя.
    """

    def __init__(self, request: Request):
        self.request = request

    async def dispatch(self):
        route = await self.request.get_route()
        user = await self.request.get_user()
        callback = UserStateCb()
        if self.request.callback:
            callback = user.state.callbacks[self.request.callback.data]
        next_route = await route.view(self.request, callback, **callback.view_params).dispatch()
        user.state.view_name = next_route.value
        await user.update()
