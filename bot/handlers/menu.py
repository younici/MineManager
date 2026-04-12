import asyncio

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command

from bot.filters.admin_filter import IsAdmin

from bot.keyboards.dynamic_kb import get_inline_kb
from bot.keyboards.menu_kb_r import menu_kb

import bot.untils.tools as tools

from main import get_server_manager

import logging

log = logging.getLogger(__name__)

router = Router(name=f"{__name__}")

mg = get_server_manager()

@router.message(IsAdmin(), F.text == "Запустить")
async def start_server_cmd(msg: Message):
    msg_text = ""
    if await mg.check_status():
        await msg.answer("Сервер уже запущен")
    else:
        await mg.start_server()
        msg_text = "Сервер запускатеся"
        msg_text += f"\nЗапускает: {msg.from_user.full_name}"
        await msg.answer(msg_text)
        await tools.notify_admins(msg.bot, msg_text, msg.from_user.id)

@router.message(IsAdmin(), F.text == "Выключить")
async def stop_server_cmd(msg: Message):
    msg_text = ""
    if await mg.check_status():
        if await mg.get_players_list():
            await msg.answer("Вы действительно хотите выключить сервер?\nНа сервере сейчас присутствуют игроки",
                              reply_markup=get_inline_kb({"Подтвердить": "close_1"}))
            return
        else:
            uptime = await mg.get_uptime()
            await mg.stop_server()
            msg_text = f"Сервер выключен, его аптайм был {uptime}"
    else:
        msg_text = "Сервер уже был выключен"
    await msg.answer(msg_text)
    msg_text += f"\nВыключает: {msg.from_user.full_name}"
    await tools.notify_admins(msg.bot, msg_text, msg.from_user.id)
        
@router.message(IsAdmin(), F.text == "Статус")
async def check_server_cmd(msg: Message):
    status = await mg.check_status()
    uptime = await mg.get_uptime()
    await msg.answer(f"Сервер {"запущен" if status else "выключен"}\nАптайм: {uptime}")

@router.message(IsAdmin(), F.text == "Логи")
async def get_logs_shortly_cmd(msg: Message):
    await _send_log(msg, await mg.get_logs())

@router.message(IsAdmin(), F.text == "Назад в меню")
async def send_menu_kb_cmd(msg: Message):
    await msg.answer("Меню", reply_markup=menu_kb)

@router.message(IsAdmin(), Command("logs"))
async def get_logs_custom_cmd(msg: Message):
    try:
        tails = int(msg.text.split(sep=" ", maxsplit=2)[1])
    except:
        tails = 50
    logs = await mg.get_logs(tails)
    await _send_log(msg, logs)

@router.callback_query(F.data.startswith("close_"), IsAdmin())
async def comfirm_close_server_cb(cb: CallbackQuery):
    data = cb.data

    uptime = await mg.get_uptime()
    await mg.stop_server()

    await cb.message.answer(f"Сервер выключается, его аптайм был {uptime}", reply_markup=menu_kb)

    msg = cb.message
    msg_text += f"Сервер выключают\nВыключает: {msg.from_user.full_name}"

    await tools.notify_admins(msg.bot, msg_text, msg.from_user.id)

async def _send_log(msg: Message, logs: str):
    if len(logs) > 1500:
        file = BufferedInputFile(logs.encode(), "logs.txt")
        await msg.answer_document(file, caption="Последние логи сервера\n\nНужны более длинные логи? отправльте команду /logs <tails-count>")
    elif logs:
        await msg.answer(f"Логи сервера:\n{logs}")
    else:
        await msg.answer("Логи пустые")

@router.message(Command("exec"), IsAdmin())
async def exec_cmd(msg: Message):
    # 1. Правильно получаем команду (отделяем /exec от остального текста)
    try:
        # maxsplit=1 разделит строку на две части: команду бота и саму команду майнкрафта
        cmd = msg.text.split(maxsplit=1)[1]
    except IndexError:
        await msg.answer("❌ Неверно введены параметры. Пример использования:\n`/exec list`", parse_mode="Markdown")
        return

    # Отправляем сообщение-заглушку, чтобы пользователь знал, что процесс пошел
    status_msg = await msg.answer("⏳ Выполняю команду...")

    try:
        # 2. ПРАВИЛЬНЫЙ вызов в отдельном потоке (функция и аргумент отдельно!)
        ret = await mg.exec_server(cmd)
        
        # 3. Защита от пустого ответа (чтобы Telegram не выдал ошибку)
        if not ret or not str(ret).strip():
            ret = "✅ Команда успешно отправлена, но сервер ничего не ответил."

        # Редактируем статусное сообщение на результат
        await status_msg.edit_text(f"```text\n{ret}\n```", parse_mode="Markdown")

    except TimeoutError:
        # Если вы добавили таймаут в Paramiko, как я советовал ранее
        await status_msg.edit_text("❌ Ошибка: сервер Minecraft не ответил на команду (TimeOut).")
    except Exception as e:
        await status_msg.edit_text(f"❌ Произошла ошибка при выполнении:\n`{e}`", parse_mode="Markdown")