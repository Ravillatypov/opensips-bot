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
        for description, vats_id, sip_regexp in await conn.fetch(
                'SELECT g.description, g.gwid, r.reg_exp FROM dr_gateways AS g '
                'JOIN re_grp AS r ON r.group_id = CAST(g.gwid AS INTEGER);'
        ):
            description = description or ''
            aor = sip_regexp.replace('^', '').replace('\\', '')
            status = reg_status.get(regs.get(aor, ''), regs.get(aor, ''))
            result.append(Reg(vats_id, description, aor, regs.get(aor, ''), status))

    return result


async def _iterate_and_send(result: List[Reg], chat_id: int):
    current = 0
    length = len(result)

    while current < length:
        await bot.send_message(
            chat_id,
            '\n'.join([f'{i.description} ({i.vats_id}): {i.status}' for i in result[current:current + 10]])
        )
        current += 10


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.trunk_list)
async def trunk_list(callback_query: CallbackQuery, **kwargs):
    # https://opensips.org/html/docs/modules/3.1.x/uac_registrant.html

    await callback_query.answer()
    result = await _get_regs()

    if result:
        await _iterate_and_send(result, callback_query.message.chat.id)

    else:
        await bot.send_message(
            callback_query.message.chat.id,
            'список пуст'
        )


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.trunk_list_fail)
async def trunk_list_fail(callback_query: CallbackQuery, **kwargs):
    # https://opensips.org/html/docs/modules/3.1.x/uac_registrant.html

    await callback_query.answer()
    result = await _get_regs()

    result = list(filter(lambda i: i.state != 'REGISTERED_STATE', result))

    if result:
        await _iterate_and_send(result, callback_query.message.chat.id)

    else:
        await bot.send_message(
            callback_query.message.chat.id,
            'Нет проблемных транков'
        )


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.trunk_list_success)
async def trunk_list_success(callback_query: CallbackQuery, **kwargs):
    # https://opensips.org/html/docs/modules/3.1.x/uac_registrant.html

    await callback_query.answer()
    result = await _get_regs()

    result = list(filter(lambda i: i.state == 'REGISTERED_STATE', result))

    if result:
        await _iterate_and_send(result, callback_query.message.chat.id)

    else:
        await bot.send_message(
            callback_query.message.chat.id,
            'список пуст'
        )
