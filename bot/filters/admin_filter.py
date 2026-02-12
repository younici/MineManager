from aiogram.filters import BaseFilter
from aiogram.types import Message
import bot.variables as vars

class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in vars.admins