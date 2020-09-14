import asyncio
import re
from typing import Tuple

from aiohttp.client import ClientSession

from app.settings import OUT_DPID_START, VOX_USERNAME, db, OSIPS_MI_URL
from app.types import Trunk


class SequenceCounter:
    def __init__(self):
        self.current = 0
        self.max_value = 2 ** 16

    @property
    def id(self) -> int:
        self.current += 1
        if self.current == self.max_value:
            self.current = 1
        return self.current


opensips_cmd_seq = SequenceCounter()


async def vats_exists(vats_id: str) -> bool:
    async with db as conn:
        vats = await conn.fetchrow('select gwid from dr_gateways where gwid = $1;', vats_id)
        return bool(vats)


async def add_dial_plan(conn, dpid, pr, match_exp, repl_exp, attrs):
    await conn.execute(
        'insert into dialplan (dpid, pr, match_op, match_exp, match_flags, repl_exp, disabled, attrs) '
        'values ($1, $2, 1, $3, 0, $4, 0, $5);',
        dpid, pr, match_exp, repl_exp, attrs
    )


async def add_trunk_to_db(trunk: Trunk) -> bool:
    async with db as conn:
        async with conn.transaction():
            out_attr = OUT_DPID_START + trunk.vats_id
            out_attr_next = OUT_DPID_START + out_attr
            await conn.execute(
                'insert into registrant '
                '(registrar, aor, username, password, binding_uri, expiry, proxy) '
                'values ($1, $2, $3, $4, $5, 180, $6);',
                trunk.domain_uri,
                trunk.sip_uri,
                trunk.username,
                trunk.password,
                trunk.local_sip_uri,
                trunk.proxy
            )
            await conn.execute(
                'insert into dr_gateways (gwid, type, address, strip, attrs, probe_mode, state, description) '
                'values ($1, 0, $2, 0, $3, 0, 0, $4);',
                f'{trunk.vats_id}',
                trunk.domain_uri,
                f'{out_attr}',
                trunk.description,
            )
            await conn.execute(
                'insert into re_grp (reg_exp, group_id) values ($1, $2)',
                '^' + re.escape(f'{trunk.sip_uri}'),
                trunk.vats_id,
            )

            await add_dial_plan(conn, out_attr, 100, '^.*', trunk.username, f'{out_attr_next}')
            await add_dial_plan(conn, out_attr_next, 100, '^.*', trunk.domain, None)
            await add_dial_plan(conn, trunk.vats_id, 1, trunk.username_regexp, VOX_USERNAME, f'{OUT_DPID_START}')
            return True


async def aio_cmd(cmd: str) -> Tuple[bool, bytes, bytes]:
    proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    return proc.returncode == 0, stdout, stderr


async def opensips_cmd(cmd: str) -> dict:
    data = {"jsonrpc": "2.0", "method": cmd, "id": opensips_cmd_seq.id}
    async with ClientSession() as session:
        async with session.post(OSIPS_MI_URL, json=data) as resp:
            if resp.status == 200:
                return await resp.json()
            raise Exception(await resp.text())
