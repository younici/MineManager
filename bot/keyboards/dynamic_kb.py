from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

def get_inline_kb(buttons: dict[str, str], rows: int = 0):
    """
    Generates an inline keyboard from a dictionary.

    Args:
        buttons (dict): Button text and callback_data {text: date}.
        rows (int): Number of buttons per row.

    Returns:
        InlineKeyboardMarkup: The finished keyboard layout.
    """
    builder = InlineKeyboardBuilder()
    
    for text, cb_data in buttons.items():
        builder.add(InlineKeyboardButton(text=text, callback_data=cb_data))

    if rows == 0:
        rows = len(buttons.items())

    builder.adjust(rows)
    
    return builder.as_markup()