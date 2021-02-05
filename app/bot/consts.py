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
    trunk_list_success = 'trunk_list_success'
    trunk_list_fail = 'trunk_list_fail'
    remove_trunk = 'remove_trunk'
    list_remove_trunk = 'list_remove_trunk'
    cancel_trunk_remove = 'cancel_trunk_remove'


class TrunkForm(StatesGroup):
    description = State()
    vats_id = State()
    domain = State()
    username = State()
    password = State()
    confirm = State()
    port = State()
    proxy = State()
