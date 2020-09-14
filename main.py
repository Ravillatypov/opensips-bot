import logging
from os import environ as env

from aiogram.utils import executor

from app.bot import dp
from app.settings import db

logging.basicConfig(level=env.get('LOG_LEVEL', 'INFO'))


async def startup(*args, **kwargs):
    await db.pool()


async def shutdown(*args, **kwargs):
    await db.close()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=startup, on_shutdown=shutdown)
