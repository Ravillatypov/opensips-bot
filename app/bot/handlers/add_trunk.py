from logging import getLogger

from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message, inline_keyboard as kb

from app.bot.consts import CallbackMethods, TrunkForm
from app.bot.misc import bot, dp
from app.bot.utils import add_keyboard
from app.types import Trunk
from app.utils import vats_exists, add_trunk as osips_add_trunk, aio_cmd

logger = getLogger(__name__)


@dp.callback_query_handler(lambda x: x.data == CallbackMethods.add_trunk)
async def add_trunk(callback_query: CallbackQuery, **kwargs):
    await callback_query.answer()
    await callback_query.message.delete()
    await bot.send_message(
        callback_query.message.chat.id,
        'Описание транка'
    )

    await TrunkForm.first()


@dp.message_handler(state=TrunkForm.description)
async def description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await TrunkForm.next()
    await bot.send_message(
        message.chat.id,
        'vats_id'
    )


@dp.message_handler(lambda m: m.text.isdigit(), state=TrunkForm.vats_id)
async def vats_id(message: Message, state: FSMContext):
    if await vats_exists(message.text):
        await state.finish()
        await add_keyboard(message.chat.id, 'Данный vats_id уже добавлен')
        return
    await state.update_data(vats_id=int(message.text))
    await TrunkForm.next()
    await bot.send_message(
        message.chat.id,
        'username'
    )


@dp.message_handler(state=TrunkForm.username)
async def username(message: Message, state: FSMContext):
    await state.update_data(username=message.text.strip())
    await TrunkForm.next()
    await bot.send_message(
        message.chat.id,
        'domain'
    )


@dp.message_handler(state=TrunkForm.domain)
async def domain(message: Message, state: FSMContext):
    await state.update_data(domain=message.text.strip())
    await TrunkForm.next()
    await bot.send_message(
        message.chat.id,
        'password'
    )


@dp.message_handler(state=TrunkForm.password)
async def password(message: Message, state: FSMContext):
    await state.update_data(password=message.text.strip())
    await TrunkForm.next()
    data = await state.get_data()

    markup = kb.InlineKeyboardMarkup()
    markup.add(kb.InlineKeyboardButton(
        'Подтвердить',
        callback_data=CallbackMethods.add_trunk_accept
    ))
    markup.add(kb.InlineKeyboardButton(
        'Отклонить',
        callback_data=CallbackMethods.add_trunk_decline
    ))

    await bot.send_message(
        message.chat.id,
        'Данные транка:\n'
        f'vats_id: {data.get("vats_id")}\n'
        f'domain: {data.get("domain")}\n'
        f'username: {data.get("username")}\n'
        f'password: {data.get("password")}\n\n'
        'Подвердите добавление транка',
        reply_markup=markup
    )


@dp.callback_query_handler(state=TrunkForm.confirm)
async def confirm(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    data = await state.get_data()
    await callback_query.answer()

    try:
        await osips_add_trunk(Trunk(
            data.get('vats_id'),
            data.get('description'),
            data.get('username'),
            data.get('domain'),
            data.get('password'),
        ))
        await aio_cmd('opensips-cli -x mi dr_reload')
        await aio_cmd('opensips-cli -x mi dp_reload')
        await aio_cmd('opensips-cli -x mi reg_reload')
    except Exception as e:
        await bot.send_message(callback_query.message.chat.id, f'Не удалось добавить. Ошибка сервера.\n\n{e}')
        logger.warning(f'{e}', exc_info=e)
    else:
        await callback_query.message.delete_reply_markup()
        await state.finish()
        await add_keyboard(callback_query.message.chat.id, 'Добавить еще транк?')
