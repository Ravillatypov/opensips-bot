import asyncio
from typing import Tuple

from aiohttp.client import ClientSession

from app.settings import OUT_DPID_START, db, OSIPS_MI_URL
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


async def add_dial_plan(conn, dpid, pr, match_op, match_exp, match_flags, repl_exp, attrs):
    await conn.execute(
        'insert into dialplan (dpid, pr, match_op, match_exp, match_flags, repl_exp, disabled, attrs) '
        'values ($1, $2, $3, $4, $5, $6, 0, $7);',
        dpid, pr, match_op, match_exp, match_flags, repl_exp, attrs,
    )


async def add_trunk_to_db(trunk: Trunk) -> bool:
    async with db as conn:
        async with conn.transaction():
            out_attr = OUT_DPID_START + trunk.vats_id
            out_attr_next = OUT_DPID_START + out_attr
            await conn.execute(
                'insert into registrant '
                '(registrar, aor, username, password, binding_uri, expiry, proxy, forced_socket, cluster_shtag) '
                'values ($1, $2, $3, $4, $5, 300, $6, $7, $8);',
                trunk.domain_uri,
                trunk.sip_uri,
                trunk.username,
                trunk.password,
                trunk.local_sip_uri,
                trunk.proxy,
                trunk.forced_socket,
                trunk.cluster_shtag,
            )
            await conn.execute(
                'insert into dr_gateways (gwid, type, address, strip, attrs, probe_mode, state, description, socket) '
                'values ($1, 0, $2, 0, $3, 0, 0, $4, $5);',
                f'{trunk.vats_id}',
                trunk.domain_uri,
                f'{out_attr}',
                trunk.description,
                trunk.forced_socket,
            )

            await add_dial_plan(conn, 100, 0, 0, trunk.match_number, 1, trunk.mdo_domain, '')
            await add_dial_plan(conn, out_attr, 100, 1, '^.*', 0, trunk.username, f'{out_attr_next}')
            await add_dial_plan(conn, out_attr_next, 100, 1, '^.*', 0, trunk.domain, '')

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
