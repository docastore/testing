from aiogram import Router, types
from aiogram.filters import Command, CommandObject

from config import ADMINS
from models.users import (
    add_saldo_by_doc,
    set_bonus_percent,
    get_bonus_percent,
)

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMINS


# ===========================
# /addsaldo DOC-ID VALOR
# ===========================
@router.message(Command("addsaldo"))
async def addsaldo_handler(msg: types.Message, command: CommandObject):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Você não é administrador.")

    if not command.args:
        return await msg.answer("Uso correto:\n/addsaldo DOC-ID valor")

    try:
        doc, valor = command.args.split()
        valor = float(valor)
    except:
        return await msg.answer("❌ Formato inválido.\nExemplo:\n/addsaldo DOC-00001 50")

    user = add_saldo_by_doc(doc, valor)
    if not user:
        return await msg.answer("❌ DOC-ID não encontrado.")

    await msg.answer(
        f"✅ Saldo adicionado!\n\n"
        f"🧾 DOC-ID: {user['doc_code']}\n"
        f"➡️ Novo saldo: R$ {user['saldo']:.2f}"
    )


# ===========================
# /setbonus %
# ===========================
@router.message(Command("setbonus"))
async def setbonus_handler(msg: types.Message, command: CommandObject):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Você não é administrador.")

    if not command.args:
        return await msg.answer("Uso correto: /setbonus 0–200")

    try:
        percent = float(command.args)
    except:
        return await msg.answer("❌ Valor inválido. Use números.")

    if percent < 0 or percent > 200:
        return await msg.answer("❌ Bônus deve ser entre 0% e 200%.")

    set_bonus_percent(percent)

    if percent == 0:
        txt = "Promoção removida."
    elif percent == 100:
        txt = "🔥 Recarga em DOBRO ativada (100%)."
    else:
        txt = f"✨ Bônus de {percent:.0f}% ativado!"

    await msg.answer(txt)


# ===========================
# /bonus – ver promoção ativa
# ===========================
@router.message(Command("bonus"))
async def bonus_info(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Você não é administrador.")

    percent = get_bonus_percent()

    if percent == 0:
        txt = "Nenhuma promoção ativa."
    elif percent == 100:
        txt = "🔥 Recarga EM DOBRO está ativa!"
    else:
        txt = f"✨ Bônus de {percent:.0f}% nas recargas está ativo."

    await msg.answer(txt)


def register_admin_handlers(dp):
    dp.include_router(router)
