from aiogram.types import Message

from app.bot.consts import CommandMethods
from app.bot.misc import bot, dp
from app.bot.utils import add_keyboard
from app.settings import ADMINS


@dp.message_handler(commands=[CommandMethods.start])
async def start(message: Message):
    if message.from_user.username not in ADMINS:
        await bot.send_message(
            message.chat.id,
            'Вы не админ!'
        )

    await add_keyboard(message.chat.id, 'Пока доступно только добавление транка')
