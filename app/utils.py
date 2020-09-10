from typing import Tuple

from app import settings
from app.types import Trunk
import asyncio


async def vats_exists(vats_id: str) -> bool:
    if not settings.db_pool:
        return True

    async with settings.db_pool.acquire() as conn:
        vats = await conn.fetchrow('select gwid from dr_gateways where gwid = $1;', vats_id)
        return bool(vats)


async def add_dial_plan(conn, dpid, pr, match_exp, repl_exp, attrs):
    await conn.execute(
        'insert into dialplan (dpid, pr, match_op, match_exp, match_flags, repl_exp, disabled, attrs) '
        'values ($1, $2, 1, $3, 0, $4, 0, $5);',
        dpid, pr, match_exp, repl_exp, attrs
    )


async def add_trunk(trunk: Trunk) -> bool:
    if not settings.db_pool:
        return False

    async with settings.db_pool.acquire() as conn:
        async with conn.transaction():
            last_attrs = await conn.fetchval('select dpid from dialplan order by dpid desc limit 1;')
            attrs = last_attrs + 1
            await conn.execute(
                'insert into registrant '
                '(registrar, aor, username, password, binding_uri, expiry) '
                'values ($1, $2, $3, $4, $5, 180);',
                f'sip:{trunk.domain}',
                f'sip:{trunk.username}@{trunk.domain}',
                f'{trunk.username}',
                f'{trunk.password}',
                f'sip:{trunk.username}@{settings.OSIPS_IP}:5060',
            )
            await conn.execute(
                'insert into dr_gateways (gwid, type, address, strip, attrs, probe_mode, state, description) '
                'values ($1, 0, $2, 0, $3, 0, 0, $4);',
                f'{trunk.vats_id}',
                f'sip:{trunk.domain}',
                f'{attrs}',
                trunk.description,
            )
            await conn.execute(
                'insert into re_grp (reg_exp, group_id) values ($1, $2)',
                f'^sip:{trunk.username}@{trunk.domain}',
                trunk.vats_id,
            )
            await add_dial_plan(conn, attrs, 100, '^.*', trunk.username, f'{attrs + 1}')
            await add_dial_plan(conn, attrs + 1, 100, '^.*', trunk.domain, None)
            await add_dial_plan(conn, attrs + 2, 1, f'^{trunk.username}', settings.VOX_USERNAME, f'{attrs + 3}')
            await add_dial_plan(conn, attrs + 3, 1, f'^{settings.OSIPS_IP}', settings.OSIPS_DOMAIN, None)
            return True


async def aio_cmd(cmd: str) -> Tuple[bool, bytes, bytes]:
    proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    return proc.returncode == 0, stdout, stderr
