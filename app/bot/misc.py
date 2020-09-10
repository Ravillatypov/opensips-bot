from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.files import JSONStorage

from app.settings import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=JSONStorage(path='/tmp/bot-state'))
