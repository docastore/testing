from aiogram import Router, types
from aiogram.filters import CommandStart

from models.users import get_or_create_user
from utils.keyboards import kb_menu_principal
from utils.texts import texto_menu_principal
from config import BANNER_FILE_ID

router = Router()


@router.message(CommandStart())
async def start_handler(msg: types.Message):
    user = get_or_create_user(msg.from_user.id)
    first = msg.from_user.first_name or "Cliente"

    caption = texto_menu_principal(user, first)

    await msg.answer_photo(
        photo=BANNER_FILE_ID,
        caption=caption,
        reply_markup=kb_menu_principal()
    )


def register_start_handlers(dp):
    dp.include_router(router)
