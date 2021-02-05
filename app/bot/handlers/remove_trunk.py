from logging import getLogger

from aiogram.types import CallbackQuery
from aiogram.types import inline_keyboard as kb

from app.bot.consts import CallbackMethods
from app.bot.misc import dp, bot
from app.settings import db
from app.utils import remove_trunk_from_db, opensips_reload_regs

logger = getLogger(__name__)


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.remove_trunk)
async def get_trunks_to_remove(callback_query: CallbackQuery, **kwargs):
    await callback_query.answer()

    offset = 0
    # TODO: добавить пагинацию, максимально кол-во 100
    markup = kb.InlineKeyboardMarkup(row_width=1)
    success = False
    async with db as conn:
        for vats_id, description in await conn.fetch(
                'SELECT g.gwid, g.description FROM dr_gateways g ;'
        ):
            markup.add(
                kb.InlineKeyboardButton(
                    f'({vats_id}) "{description}"',
                    callback_data=f'trunk_remove_{vats_id}'
                )
            )

            if len(markup.inline_keyboard) == 50:
                markup.add(
                    kb.InlineKeyboardButton(
                        'Отмена',
                        callback_data=CallbackMethods.cancel_trunk_remove
                    )
                )

                await bot.send_message(
                    callback_query.message.chat.id,
                    'Выберите транк для удаления',
                    reply_markup=markup
                )

                markup = kb.InlineKeyboardMarkup(row_width=1)
                success = True

    if markup.inline_keyboard:
        markup.add(
            kb.InlineKeyboardButton(
                'Отмена',
                callback_data=CallbackMethods.cancel_trunk_remove
            )
        )

        await bot.send_message(
            callback_query.message.chat.id,
            'Выберите транк для удаления',
            reply_markup=markup
        )

    elif not success:
        return await bot.send_message(
            callback_query.message.chat.id,
            'Нет транков для удаления'
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
        row = await conn.fetchrow(
            ''' SELECT g.description, r.username, trim(leading 'sip:' from r.registrar) as domian, r."password" '''
            'FROM dr_gateways AS g '
            'LEFT OUTER JOIN registrant r ON r.id = g.id WHERE g.gwid = $1; ',
            f'{vats_id}'
        )

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
