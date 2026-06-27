from aiogram.fsm.state import StatesGroup, State

class AdminStates(StatesGroup):
    waiting_for_id = State()
    waiting_for_amount = State()
    waiting_for_post = State()