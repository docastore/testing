from aiogram.fsm.state import StatesGroup, State


class AddStockState(StatesGroup):
    waiting_tipo = State()        # AMZ_DIG, AMZ_MIX, etc
    waiting_email = State()
    waiting_senha = State()
    waiting_images = State()      # recebe múltiplas imagens
    waiting_tutorial = State()
