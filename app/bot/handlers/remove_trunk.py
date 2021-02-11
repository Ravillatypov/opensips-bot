from logging import getLogger
from math import ceil

from aiogram.types import CallbackQuery
from aiogram.types import inline_keyboard as kb

from app.bot.consts import CallbackMethods
from app.bot.misc import dp, bot
from app.settings import db
from app.utils import remove_trunk_from_db, opensips_reload_regs

logger = getLogger(__name__)
_PAGE_SIZE = 10


async def _get_gateways_count() -> int:
    async with db as conn:
        row = await conn.fetchrow('SELECT count(1) as count FROM dr_gateways;')

    return row[0]


async def _get_trunks_list_markup(page: int) -> kb.InlineKeyboardMarkup:
    markup = kb.InlineKeyboardMarkup(row_width=3)
    offset = (page - 1) * _PAGE_SIZE

    async with db as conn:
        for vats_id, description in await conn.fetch(
                f'SELECT g.gwid, g.description FROM dr_gateways g offset {offset} limit {_PAGE_SIZE} ;'
        ):
            markup.add(
                kb.InlineKeyboardButton(
                    f'({vats_id}) "{description}"',
                    callback_data=f'trunk_remove_{vats_id}'
                )
            )

    if not markup.inline_keyboard:
        return markup

    count = await _get_gateways_count()
    pages = ceil(count / _PAGE_SIZE)

    if page > 1:
        markup.add(
            kb.InlineKeyboardButton(
                '<<',
                callback_data=f'remove_trunk_page_{page - 1}'
            )
        )

    markup.add(
        kb.InlineKeyboardButton(
            'Отмена',
            callback_data=CallbackMethods.cancel_trunk_remove
        )
    )

    if pages > page:
        markup.add(
            kb.InlineKeyboardButton(
                '>>',
                callback_data=f'remove_trunk_page_{page + 1}'
            )
        )

    return markup


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.remove_trunk)
async def get_trunks_to_remove(callback_query: CallbackQuery, **kwargs):
    await callback_query.answer()

    page = 1
    markup = await _get_trunks_list_markup(page)

    if not markup.inline_keyboard:
        return await bot.send_message(
            callback_query.message.chat.id,
            'Нет транков для удаления'
        )

    await bot.send_message(
        callback_query.message.chat.id,
        'Выберите транк для удаления',
        reply_markup=markup
    )


@dp.callback_query_handler(lambda c: c.data.startswith('remove_trunk_page_'))
async def get_remove_trunk_page(callback_query: CallbackQuery, **kwargs):
    await callback_query.answer()
    page = int(callback_query.data.replace('remove_trunk_page_', ''))
    markup = await _get_trunks_list_markup(page)
    if markup.inline_keyboard:
        await bot.edit_message_reply_markup(
            callback_query.message.chat.id, callback_query.message.message_id, reply_markup=markup
        )


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.cancel_trunk_remove)
async def cancel_trunk_remove(callback_query: CallbackQuery, **kwargs):
    await callback_query.answer()
    await callback_query.message.delete()


@dp.callback_query_handler(lambda c: c.data.startswith('trunk_remove_'))
async def select_trunk_to_remove(callback_query: CallbackQuery, **kwargs):
    await callback_query.answer()
    await callback_query.message.delete()

    vats_id = int(callback_query.data.replace('trunk_remove_', ''))

    async with db as conn:
        sql = (
            ''' SELECT g.description, r.username, trim(leading 'sip:' from r.registrar) as domian, r."password" '''
            'FROM dr_gateways AS g '
            'LEFT OUTER JOIN registrant r ON r.id = g.id WHERE g.gwid = $1; '
        )
        row = await conn.fetchrow(sql, f'{vats_id}')

    if row is not None:
        description, username, domain, password = row
    else:
        return await bot.send_message(
            callback_query.message.chat.id,
            'Что-то пошло не так...\nНе удалось получить данные по транку'
        )

    markup = kb.InlineKeyboardMarkup()
    markup.add(
        kb.InlineKeyboardButton(
            'Да, удалить',
            callback_data=f'remove_trunk_confirm_{vats_id}'
        )
    )

    markup.add(
        kb.InlineKeyboardButton(
            'Отмена',
            callback_data=CallbackMethods.cancel_trunk_remove
        )
    )

    await bot.send_message(
        callback_query.message.chat.id,
        ('Внимание! Вы уверены, что хотите удалить данную запись?\n'
         f'Описание: {description}\n'
         f'vats_id: {vats_id}\n'
         f'domain: {domain}\n'
         f'username: {username}\n'
         f'password: {password}\n'),
        reply_markup=markup,
    )


@dp.callback_query_handler(lambda c: c.data.startswith('remove_trunk_confirm_'))
async def remove_trunk_confirm(callback_query: CallbackQuery, **kwargs):
    await callback_query.answer()
    await callback_query.message.delete()

    vats_id = int(callback_query.data.replace('remove_trunk_confirm_', ''))

    await remove_trunk_from_db(vats_id)
    await opensips_reload_regs()
