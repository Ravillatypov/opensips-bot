from logging import getLogger

from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.consts import CallbackMethods, TrunkForm
from app.bot.misc import bot, dp
from app.bot.utils import add_keyboard, send_confirm_message, delete_callback_message
from app.settings import OUT_DPID_START, ADMINS
from app.types import Trunk
from app.utils import vats_exists, opensips_reload_regs, add_trunk_to_db

logger = getLogger(__name__)


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
    if int(message.text) >= OUT_DPID_START:
        await bot.send_message(
            message.chat.id,
            'vats_id не может быть больше 9999'
        )

    if await vats_exists(message.text):
        await state.finish()
        await add_keyboard(message.chat.id, 'Данный vats_id уже добавлен')
        return
    await state.update_data(vats_id=int(message.text))
    await TrunkForm.next()
    await bot.send_message(
        message.chat.id,
        'domain'
    )


@dp.message_handler(state=TrunkForm.username)
async def username(message: Message, state: FSMContext):
    await state.update_data(username=message.text.strip())
    await TrunkForm.next()
    await bot.send_message(
        message.chat.id,
        'password'
    )


@dp.message_handler(state=TrunkForm.external_number)
async def external_number(message: Message, state: FSMContext):
    await state.update_data(external_number=message.text.strip())
    await TrunkForm.next()
    await bot.send_message(
        message.chat.id,
        'username'
    )


@dp.message_handler(state=TrunkForm.domain)
async def domain(message: Message, state: FSMContext):
    await state.update_data(domain=message.text.strip())
    await TrunkForm.next()
    await bot.send_message(
        message.chat.id,
        'external_number'
    )


@dp.message_handler(state=TrunkForm.password)
async def password(message: Message, state: FSMContext):
    await state.update_data(password=message.text.strip())
    await TrunkForm.next()
    data = await state.get_data()
    await send_confirm_message(message.chat.id, data)


@dp.message_handler(lambda m: m.text.isdigit(), state=TrunkForm.port)
async def port(message: Message, state: FSMContext):
    await state.update_data(port=int(message.text.strip()))
    await TrunkForm.confirm.set()
    await send_confirm_message(
        message.chat.id,
        await state.get_data()
    )


@dp.message_handler(state=TrunkForm.proxy)
async def proxy(message: Message, state: FSMContext):
    await state.update_data(proxy=message.text.strip())
    await TrunkForm.confirm.set()
    await send_confirm_message(
        message.chat.id,
        await state.get_data()
    )


# Callbacks

@dp.callback_query_handler(lambda x: x.data == CallbackMethods.add_trunk)
async def add_trunk(callback_query: CallbackQuery, **kwargs):
    await callback_query.answer()
    await delete_callback_message(callback_query)

    if callback_query.message.chat.username not in ADMINS:
        await bot.send_message(
            callback_query.message.chat.id,
            'Вы не админ!'
        )
        return

    await bot.send_message(
        callback_query.message.chat.id,
        'Описание транка'
    )

    await TrunkForm.first()


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.add_trunk_decline, state=TrunkForm.confirm)
async def decline(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    await state.finish()
    await callback_query.answer()
    await delete_callback_message(callback_query)
    await add_keyboard(callback_query.message.chat.id, 'Добавить еще транк?')


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.add_trunk_port, state=TrunkForm.confirm)
async def port_callback(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    await callback_query.answer()
    await delete_callback_message(callback_query)
    await bot.send_message(
        callback_query.message.chat.id,
        'Введите номер порта'
    )
    await TrunkForm.port.set()


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.add_trunk_proxy, state=TrunkForm.confirm)
async def proxy_callback(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    await callback_query.answer()
    await delete_callback_message(callback_query)
    await bot.send_message(
        callback_query.message.chat.id,
        'Введите прокси. Например: sip.sbc.ru:5665'
    )
    await TrunkForm.proxy.set()


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.add_trunk_accept, state=TrunkForm.confirm)
async def confirm(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    data = await state.get_data()
    await callback_query.answer()

    if callback_query.message.chat.username not in ADMINS:
        await bot.send_message(
            callback_query.message.chat.id,
            'Вы не админ!'
        )
        await state.finish()
        return

    try:
        port_number = f":{data.get('port')}" if data.get('port') else ''
        proxy_uri = f"sip:{data.get('proxy')}" if data.get('proxy') else None
        await add_trunk_to_db(Trunk(
            data.get('vats_id'),
            data.get('description'),
            data.get('username'),
            data.get('domain'),
            data.get('password'),
            port_number,
            proxy_uri,
            data.get('external_number'),
        ))
        await opensips_reload_regs()
    except Exception as e:
        await bot.send_message(callback_query.message.chat.id, f'Не удалось добавить. Ошибка сервера.\n\n{e}')
        logger.warning(f'{e}', exc_info=e)
    else:
        await callback_query.message.delete_reply_markup()
        await add_keyboard(callback_query.message.chat.id, 'Добавить еще транк?')

    await state.finish()
