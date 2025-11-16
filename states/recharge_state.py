# states/recharge_state.py
from aiogram.fsm.state import StatesGroup, State


class RechargeState(StatesGroup):
    waiting_amount = State()
