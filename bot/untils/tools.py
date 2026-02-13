from aiogram import Bot

import bot.variables as vars

import logging

__log = logging.getLogger(__name__)

async def notify_admins(bot: Bot, msg: str, sender_id: int | None):
    admins_id = vars.admins

    if sender_id: admins_id.remove(sender_id)

    for admin_id in admins_id:
        try:
            await bot.send_message(admin_id, msg)
        except Exception as e:
            __log.error(e)

async def get_name(bot: Bot, id: int) -> str | None:
    try:
        chat = await bot.get_chat(id)
        return chat.full_name
    except:
        return None