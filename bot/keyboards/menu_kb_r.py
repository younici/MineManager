from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Запустить")],
        [KeyboardButton(text="Выключить")],
        [KeyboardButton(text="Статус")],
        [KeyboardButton(text="Логи")],
        [KeyboardButton(text="Другие действия...")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выбери действие"
)