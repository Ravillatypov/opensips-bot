from logging import getLogger

from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message, inline_keyboard as kb

from app.bot.consts import CallbackMethods, TrunkForm
from app.bot.misc import bot, dp
from app.bot.utils import add_keyboard
from app.types import Trunk
from app.utils import vats_exists, add_trunk as osips_add_trunk, opensips_cmd

logger = getLogger(__name__)


async def send_confirm_message(chat_id, data):
    markup = kb.InlineKeyboardMarkup()
    markup.add(kb.InlineKeyboardButton(
        'Подтвердить',
        callback_data=CallbackMethods.add_trunk_accept
    ))
    markup.add(kb.InlineKeyboardButton(
        'Отклонить',
        callback_data=CallbackMethods.add_trunk_decline
    ))
    markup.add(kb.InlineKeyboardButton(
        'Указать порт',
        callback_data=CallbackMethods.add_trunk_port
    ))
    markup.add(kb.InlineKeyboardButton(
        'Указать прокси',
        callback_data=CallbackMethods.add_trunk_proxy
    ))

    message = ('Данные транка:\n'
               f'vats_id: {data.get("vats_id")}\n'
               f'domain: {data.get("domain")}\n'
               f'username: {data.get("username")}\n'
               f'password: {data.get("password")}\n'
               '',)

    if data.get('port'):
        message += f'port: {data.get("port")}\n'

    if data.get('proxy'):
        message += f'proxy: {data.get("proxy")}\n'

    await bot.send_message(
        chat_id,
        f'{message}\nПодвердите добавление транка',
        reply_markup=markup
    )


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
    await send_confirm_message(message.chat.id, data)


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.add_trunk_decline, state=TrunkForm.confirm)
async def decline(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    await state.finish()
    await callback_query.message.delete()
    await add_keyboard(callback_query.message.chat.id, 'Добавить еще транк?')


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.add_trunk_port, state=TrunkForm.confirm)
async def port_callback(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    await callback_query.message.delete()
    await bot.send_message(
        callback_query.message.chat.id,
        'Введите номер порта'
    )
    await TrunkForm.port.set()


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.add_trunk_proxy, state=TrunkForm.confirm)
async def proxy_callback(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    await callback_query.message.delete()
    await bot.send_message(
        callback_query.message.chat.id,
        'Введите прокси. Например: sip.sbc.ru:5665'
    )
    await TrunkForm.proxy.set()


@dp.callback_query_handler(lambda c: c.data == CallbackMethods.add_trunk_accept, state=TrunkForm.confirm)
async def confirm(callback_query: CallbackQuery, state: FSMContext, **kwargs):
    data = await state.get_data()
    await callback_query.answer()

    try:
        port_number = f":{data.get('port')}" if data.get('port') else ''
        proxy_uri = f"sip:{data.get('proxy')}" if data.get('proxy') else None
        await osips_add_trunk(Trunk(
            data.get('vats_id'),
            data.get('description'),
            data.get('username'),
            data.get('domain'),
            data.get('password'),
            port_number,
            proxy_uri
        ))
        await opensips_cmd('dr_reload')
        await opensips_cmd('dp_reload')
        await opensips_cmd('reg_reload')
    except Exception as e:
        await bot.send_message(callback_query.message.chat.id, f'Не удалось добавить. Ошибка сервера.\n\n{e}')
        logger.warning(f'{e}', exc_info=e)
    else:
        await callback_query.message.delete_reply_markup()
        await state.finish()
        await add_keyboard(callback_query.message.chat.id, 'Добавить еще транк?')


@dp.message_handler(lambda m: m.text.isdigit(), state=TrunkForm.port)
async def port(message: Message, state: FSMContext):
    await state.update_data(port=int(message.text.strip()))
    await TrunkForm.confirm.set()
    await send_confirm_message(
        message.chat.id,
        await state.get_data()
    )


@dp.message_handler(state=TrunkForm.proxy)
async def port(message: Message, state: FSMContext):
    await state.update_data(proxy=message.text.strip())
    await TrunkForm.confirm.set()
    await send_confirm_message(
        message.chat.id,
        await state.get_data()
    )
