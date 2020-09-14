from aiogram.dispatcher.filters.state import State, StatesGroup


class CommandMethods:
    start = 'start'


class CallbackMethods:
    add_trunk = 'add_trunk'
    add_trunk_accept = 'add_trunk_accept'
    add_trunk_decline = 'add_trunk_decline'
    add_trunk_port = 'add_trunk_port'
    add_trunk_proxy = 'add_trunk_proxy'
    trunk_list = 'trunk_list'


class TrunkForm(StatesGroup):
    description = State()
    vats_id = State()
    username = State()
    domain = State()
    password = State()
    confirm = State()
    port = State()
    proxy = State()
