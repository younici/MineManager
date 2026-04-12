from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command

from bot.filters.admin_filter import IsAdmin
from bot.keyboards.extended_kb_r import extended_kb

from main import get_server_manager

import logging

log = logging.getLogger(__name__)

router = Router(name=f"{__name__}")

mg = get_server_manager()

@router.message(IsAdmin(), F.text == "Список игроков на сервере")
async def send_player_list_cmd(msg: Message):
    if not await mg.check_status():
        await msg.answer("Сервер не запущен")
        return

    players_list = await mg.get_players_list()
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
    await mg.clear_logs()
    await msg.answer("Логи были очищены")

@router.message(IsAdmin(), F.text == "Аптайм")
async def send_uptime_server_cmd(msg: Message):
    await msg.answer(await mg.get_uptime())

@router.message(IsAdmin(), F.text == "Другие действия...")
async def send_extended_kb_cmd(msg: Message):
    await msg.answer("Расширеное меню", reply_markup=extended_kb)

@router.message(IsAdmin(), F.text == "Логи")
async def get_logs_shortly_cmd(msg: Message):
    await _send_log(msg, await mg.get_logs())

@router.message(IsAdmin(), Command("logs"))
async def get_logs_custom_cmd(msg: Message):
    try:
        tails = int(msg.text.split(sep=" ", maxsplit=2)[1])
    except:
        tails = 50
    logs = await mg.get_logs(tails)
    await _send_log(msg, logs)

async def _send_log(msg: Message, logs: str):
    if len(logs) > 1500:
        file = BufferedInputFile(logs.encode(), "logs.txt")
        await msg.answer_document(file, caption="Последние логи сервера\n\nНужны более длинные логи? отправльте команду /logs <tails-count>")
    elif logs:
        await msg.answer(f"Логи сервера:\n{logs}")
    else:
        await msg.answer("Логи пустые")