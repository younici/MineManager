from aiogram import Router, F
from aiogram.types import Message

from bot.filters.admin_filter import IsAdmin

from bot.keyboards.extended_kb_r import extended_kb

from main import get_server_manager

import logging

log = logging.getLogger(__name__)

router = Router(name=f"{__name__}")

mg = get_server_manager()

@router.message(IsAdmin(), F.text == "Список игроков на сервере")
async def send_player_list_cmd(msg: Message):
    if not mg.check_status():
        await msg.answer("Сервер не запущен")
        return

    players_list = mg.get_players_list()
    log.info(players_list)
    if players_list:
        players: str = ""
        for player in players_list:
            players += player + "\n"
        await msg.answer(f"Список игроков на сервере:\n{players}")
    else:
        await msg.answer("На сервере сейчас никого нету")

@router.message(IsAdmin(), F.text == "Очистить логи сервера")
async def clear_logs_cmd(msg: Message):
    mg.clear_logs()
    await msg.answer("Логи были очищены")

@router.message(IsAdmin(), F.text == "Аптайм")
async def send_uptime_server_cmd(msg: Message):
    await msg.answer(mg.get_uptime())

@router.message(IsAdmin(), F.text == "Другие действия...")
async def send_extended_kb_cmd(msg: Message):
    await msg.answer("Расширеное меню", reply_markup=extended_kb)