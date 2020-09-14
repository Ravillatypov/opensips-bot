import re
from typing import List

from aiogram.types import CallbackQuery

from app import settings
from app.bot.consts import CallbackMethods
from app.bot.misc import dp, bot
from app.utils import opensips_cmd


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


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.trunk_list)
async def trunk_list(callback_query: CallbackQuery, **kwargs):
    # https://opensips.org/html/docs/modules/3.1.x/uac_registrant.html

    result = []
    reg_list = await opensips_cmd('reg_list')
    reg_list = reg_list.get('result', {}).get('Records', [])
    regs = {'^' + re.escape(i.get('AOR', '')): i.get('state') for i in reg_list}

    async with settings.db_pool as conn:
        for description, vats_id, sip_regexp in await conn.fetch(
                'SELECT g.description, g.gwid, r.reg_exp FROM dr_gateways AS g '
                'JOIN re_grp AS r ON r.group_id = CAST(g.gwid AS INTEGER);'
        ):
            description = description or ''
            status = reg_status.get(regs.get(sip_regexp, ""))
            result.append(f'{description} ({vats_id}): {status}')

    if result:
        text = '\n'.join(result)
    else:
        text = 'список пуст'

    await bot.send_message(
        callback_query.message.chat.id,
        text
    )
