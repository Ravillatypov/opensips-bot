from aiogram.types import inline_keyboard as kb

from app.bot.consts import CallbackMethods
from app.bot.misc import bot


async def add_keyboard(chat_id: int, message: str):
    markup = kb.InlineKeyboardMarkup()
    markup.add(kb.InlineKeyboardButton(
        'Добавить транк',
        callback_data=CallbackMethods.add_trunk
    ))

    await bot.send_message(
        chat_id,
        message,
        reply_markup=markup,
    )
