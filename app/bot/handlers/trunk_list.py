from collections import namedtuple
from logging import getLogger
from typing import List

from aiogram.types import CallbackQuery

from app.bot.consts import CallbackMethods
from app.bot.misc import dp, bot
from app.settings import db
from app.utils import opensips_cmd

logger = getLogger(__name__)

reg_status = {
    'NOT_REGISTERED_STATE': 'в процессе',
    'REGISTERING_STATE': 'в процессе',
    'AUTHENTICATING_STATE': 'в процессе',
    'REGISTERED_STATE': 'зарегистрирован',
    'REGISTER_TIMEOUT_STATE': 'не дождались ответа',
    'INTERNAL_ERROR_STATE': 'внутренняя ошибка',
    'WRONG_CREDENTIALS_STATE': 'неправильные данные',
    'REGISTRAR_ERROR_STATE': 'ошибка при регистрации',
}

Reg = namedtuple('Reg', ['vats_id', 'description', 'aor', 'state', 'status'])


async def _get_regs() -> List[Reg]:
    result = []
    reg_list = await opensips_cmd('reg_list')
    reg_list = reg_list.get('result', {}).get('Records', [])
    regs = {i.get('AOR', ''): i.get('state', '') for i in reg_list}

    async with db as conn:
        for vats_id, description, aor in await conn.fetch(
                '''SELECT g.gwid, g.description, 'sip:' || d.repl_exp || '@' || d2.repl_exp as aor '''
                'FROM dr_gateways g '
                'JOIN dialplan d ON CAST(g.attrs AS INTEGER) = d.dpid '
                'JOIN dialplan d2 ON CAST(d2.dpid AS TEXT) = d.attrs;'
        ):
            description = description or ''
            status = reg_status.get(regs.get(aor, ''), regs.get(aor, '')) or ''
            result.append(Reg(vats_id, description, aor, regs.get(aor, ''), status))

    return result


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.trunk_list)
async def trunk_list(callback_query: CallbackQuery, **kwargs):
    # https://opensips.org/html/docs/modules/3.1.x/uac_registrant.html

    await callback_query.answer()
    result = await _get_regs()
    text = ''

    if result:
        text = '\n'.join([f'{i.description} ({i.vats_id}): {i.status}' for i in result])

    await bot.send_message(
        callback_query.message.chat.id,
        text or 'список пуст'
    )


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.trunk_list_fail)
async def trunk_list_fail(callback_query: CallbackQuery, **kwargs):
    # https://opensips.org/html/docs/modules/3.1.x/uac_registrant.html

    await callback_query.answer()
    result = await _get_regs()
    text = ''

    if result:
        text = '\n'.join(
            [f'{i.description} ({i.vats_id}): {i.status}' for i in result if i.state != 'REGISTERED_STATE']
        )

    await bot.send_message(
        callback_query.message.chat.id,
        text or 'Нет проблемных транков'
    )


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.trunk_list_success)
async def trunk_list_success(callback_query: CallbackQuery, **kwargs):
    # https://opensips.org/html/docs/modules/3.1.x/uac_registrant.html

    await callback_query.answer()
    result = await _get_regs()
    text = ''

    if result:
        text = '\n'.join(
            [f'{i.description} ({i.vats_id}): {i.status}' for i in result if i.state == 'REGISTERED_STATE']
        )

    await bot.send_message(
        callback_query.message.chat.id,
        text or 'список пуст'
    )
