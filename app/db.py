from asyncio import sleep

from asyncpg.connection import Connection
from asyncpg.pool import Pool, create_pool


class DB:
    __pool: Pool = None

    def __init__(self, dsn: str):
        self.dsn = dsn
        self.__connection = None

    async def pool(self) -> Pool:
        if not isinstance(self.__pool, Pool):
            self.__pool = await create_pool(self.dsn)

        if self.__pool._closed or self.__pool._closing:
            self.__pool = await create_pool(self.dsn)

        return self.__pool

    async def close(self):
        await self.__pool.close()

    async def __aenter__(self) -> Connection:
        counter = 0
        while self.__connection is not None:
            await sleep(1)
            counter += 1
            if counter >= 20:
                raise Exception('connection is not ready')

        pool = await self.pool()
        self.__connection = await pool.acquire().__aenter__()
        return self.__connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        con = self.__connection
        self.__connection = None
        pool = await self.pool()
        await pool.release(con)
