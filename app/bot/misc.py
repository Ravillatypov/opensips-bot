from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.files import JSONStorage

from app.settings import TOKEN, LOCAL_DB_PATH

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=JSONStorage(path=LOCAL_DB_PATH))
