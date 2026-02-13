from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.keyboards.menu_kb_r import menu_kb

from bot.filters.admin_filter import IsAdmin

import bot.variables as vars
import bot.untils.tools as tools

_HELP_MSG = """
test
test
test
"""

router = Router(name=f"{__name__}")

@router.message(Command("start"), IsAdmin())
async def start_cmd(msg: Message):
    await msg.answer("Приветствуем, бот создан для управления сервером, вы были указаны как Администратор", reply_markup=menu_kb)

@router.message(Command("help"), IsAdmin())
async def help_cmd(msg: Message):
    await msg.answer(_HELP_MSG)

@router.message(Command("menu"), IsAdmin())
async def show_menu_cmd(msg: Message):
    await msg.answer("Меню", reply_markup=menu_kb)

@router.message(Command("admins_list"), IsAdmin())
async def send_admins_list(msg: Message):
    msg_text = ""

    for id in vars.admins:
        full_name = await tools.get_name(msg.bot, id)
        msg_text += f"{full_name}: {id}\n"

    await msg.answer(msg_text)