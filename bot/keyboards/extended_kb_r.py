from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

extended_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Назад в меню")],
        [KeyboardButton(text="Очистить логи сервера")],
        [KeyboardButton(text="Список игроков на сервере")],
        [KeyboardButton(text="Аптайм")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие"
)