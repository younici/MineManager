from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.filters.admin_filter import IsAdmin

from bot.keyboards.dynamic_kb import get_inline_kb
from bot.keyboards.menu_kb_r import menu_kb

from bot.handlers._tools import send_log

from main import get_server_manager

import logging

log = logging.getLogger(__name__)

router = Router(name=f"{__name__}")

mg = get_server_manager()

@router.message(IsAdmin(), F.text == "Запустить")
async def start_server_cmd(msg: Message):
    if mg.check_status():
        await msg.answer("Сервер уже запущен")
    else:
        mg.start_server()
        await msg.answer("Сервер запускатеся")

@router.message(IsAdmin(), F.text == "Остановить")
async def stop_server_cmd(msg: Message):
    if mg.check_status():
        if mg.get_players_list():
            await msg.answer("Вы действительно хотите остановить сервер?\nНа сервере сейчас присутствуют игроки",
                              reply_markup=get_inline_kb({"Подтвердить": "close_1"}))
            return
        else:
            uptime = mg.get_uptime()
            mg.stop_server()
            await msg.answer(f"Сервер остановлен, его аптайм был {uptime}")
    else:
        await msg.answer("Сервер уже был остановлен")

@router.message(IsAdmin(), F.text == "Статус")
async def check_server_cmd(msg: Message):
    status = mg.check_status()
    uptime = mg.get_uptime()
    await msg.answer(f"Сервер {"запущен" if status else "остановлен"}\nАптайм: {uptime}")

@router.message(IsAdmin(), F.text == "Логи")
async def get_logs_shortly_cmd(msg: Message):
    await send_log(msg, mg.get_logs())

@router.message(IsAdmin(), F.text == "Назад в меню")
async def send_menu_kb_cmd(msg: Message):
    await msg.answer("Меню", reply_markup=menu_kb)

@router.message(IsAdmin(), Command("logs"))
async def get_logs_custom_cmd(msg: Message):
    try:
        tails = int(msg.text.split(sep=" ", maxsplit=2)[1])
    except:
        tails = 50
    logs = mg.get_logs(tails)
    await send_log(msg, logs)

@router.callback_query(F.data.startswith("close_"), IsAdmin())
async def comfirm_close_server_cb(cb: CallbackQuery):
    data = cb.data
    action = data.split(sep="_")[1]

    if action == "1":
        uptime = mg.get_uptime()
        mg.stop_server()
        await cb.message.answer(f"Сервер остановлен, его аптайм был {uptime}", reply_markup=menu_kb)