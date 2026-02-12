from aiogram.types import Message, BufferedInputFile

async def send_log(msg: Message, logs: str):
    if len(logs) > 1500:
        file = BufferedInputFile(logs.encode(), "logs.txt")
        await msg.answer_document(file, caption="Последние логи сервера\n\nНужны более длинные логи? отправльте команду /logs <tails-count>")
    elif logs:
        await msg.answer(f"Логи сервера:\n{logs}")
    else:
        await msg.answer("Логи пустые")

