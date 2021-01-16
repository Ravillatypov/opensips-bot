from aiogram.types import CallbackQuery
from aiogram.types import inline_keyboard as kb

from app.bot.consts import CallbackMethods
from app.bot.misc import dp, bot
from app.settings import db
from app.utils import remove_trunk_from_db, opensips_reload_regs


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.remove_trunk)
async def get_trunks_to_remove(callback_query: CallbackQuery, **kwargs):
    await callback_query.answer()

    markup = kb.InlineKeyboardMarkup()
    async with db as conn:
        for vats_id, description in await conn.fetch(
                'SELECT g.gwid, g.description FROM dr_gateways g ;'
        ):
            markup.add(
                kb.InlineKeyboardButton(
                    f'удалить "{description}" ({vats_id})',
                    callback_data=f'trunk_remove_{vats_id}'
                )
            )

    if not markup.inline_keyboard:
        return await bot.send_message(
            callback_query.message.chat.id,
            'нет транков для удаления'
        )

    markup.add(
        kb.InlineKeyboardButton(
            f'отмена',
            callback_data=CallbackMethods.cancel_trunk_remove
        )
    )

    await bot.send_message(
        callback_query.message.chat.id,
        'Выбирите транк для удаления',
        reply_markup=markup
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

    await remove_trunk_from_db(vats_id)
    await opensips_reload_regs()
