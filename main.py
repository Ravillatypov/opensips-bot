import logging
from os import environ as env
from app.bot import dp
from aiogram.utils import executor
from app import settings

from asyncpg import create_pool

logging.basicConfig(level=env.get('LOG_LEVEL', 'INFO'))


async def startup(*args, **kwargs):
    settings.db_pool = await create_pool(settings.DB_DSN)


async def shutdown(*args, **kwargs):
    await settings.db_pool.close()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=startup, on_shutdown=shutdown)
