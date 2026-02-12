from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.redis import RedisStorage

from redis.asyncio import Redis

import bot.variables as variables

import bot.handlers as handlers

import pkgutil
import importlib

async def start(token: str, tg_admins: list[int], redis: Redis | None):
    storage = RedisStorage(redis) if redis else None
    dp = Dispatcher(storage=storage)
    bot = Bot(token)

    for _, module_name, _ in pkgutil.iter_modules(handlers.__path__):
        full_module_name = f"bot.handlers.{module_name}"
        module = importlib.import_module(full_module_name)
        
        if hasattr(module, "router") and isinstance(module.router, Router):
            dp.include_router(module.router)

    variables.admins = tg_admins

    await dp.start_polling(bot)