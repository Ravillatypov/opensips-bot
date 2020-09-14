from aiogram.types import inline_keyboard as kb

from app.bot.consts import CallbackMethods
from app.bot.misc import bot


async def add_keyboard(chat_id: int, message: str):
    markup = kb.InlineKeyboardMarkup()
    markup.add(kb.InlineKeyboardButton(
        'Добавить транк',
        callback_data=CallbackMethods.add_trunk
    ))
    markup.add(kb.InlineKeyboardButton(
        'Список транков',
        callback_data=CallbackMethods.trunk_list
    ))

    await bot.send_message(
        chat_id,
        message,
        reply_markup=markup,
    )


async def send_confirm_message(chat_id, data):
    markup = kb.InlineKeyboardMarkup()
    markup.add(kb.InlineKeyboardButton(
        'Подтвердить',
        callback_data=CallbackMethods.add_trunk_accept
    ))
    markup.add(kb.InlineKeyboardButton(
        'Отклонить',
        callback_data=CallbackMethods.add_trunk_decline
    ))
    markup.add(kb.InlineKeyboardButton(
        'Указать порт',
        callback_data=CallbackMethods.add_trunk_port
    ))
    markup.add(kb.InlineKeyboardButton(
        'Указать прокси',
        callback_data=CallbackMethods.add_trunk_proxy
    ))

    message = ('Данные транка:\n'
               f'vats_id: {data.get("vats_id")}\n'
               f'domain: {data.get("domain")}\n'
               f'username: {data.get("username")}\n'
               f'password: {data.get("password")}\n')

    if data.get('port'):
        message += f'port: {data.get("port")}\n'

    if data.get('proxy'):
        message += f'proxy: {data.get("proxy")}\n'

    await bot.send_message(
        chat_id,
        f'{message}\nПодвердите добавление транка',
        reply_markup=markup
    )
