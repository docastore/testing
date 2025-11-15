from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import ADMINS
from states.add_stock_state import AddStockState
from models.stock import create_stock, add_stock_image
from utils.texts import TUTORIAL_PADRAO

router = Router()


def is_admin(uid: int) -> bool:
    return uid in ADMINS


# ===========================
# /addstock TIPO (continua funcionando)
# ===========================
@router.message(Command("addstock"))
async def addstock_start_cmd(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Você não é administrador.")

    args = msg.text.split()
    if len(args) < 2:
        return await msg.answer(
            "Uso correto:\n\n/addstock AMZ_DIG\n/addstock AMZ_MIX\n/addstock AMZ_PRIME\n/addstock AMZ_10P"
        )

    tipo = args[1].strip().upper()
    await iniciar_fluxo_addstock(msg, state, tipo)


# ===========================
# Início do fluxo vindo de botão (adm_add_AMZ_XXX)
# ===========================
@router.callback_query(F.data.startswith("adm_add_"))
async def addstock_start_button(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Você não é admin.", show_alert=True)

    tipo = callback.data.replace("adm_add_", "").strip().upper()
    await iniciar_fluxo_addstock(callback.message, state, tipo)
    await callback.answer()


async def iniciar_fluxo_addstock(message: types.Message, state: FSMContext, tipo: str):
    # Limpa estado anterior
    await state.clear()

    await state.update_data(tipo=tipo, imagens=[])

    await message.answer(
        f"📦 Iniciando cadastro de estoque para o tipo *{tipo}*\n\n"
        "Digite o *email* da conta:"
    )
    await state.set_state(AddStockState.waiting_email)


# ===========================
# EMAIL
# ===========================
@router.message(AddStockState.waiting_email)
async def addstock_email(msg: types.Message, state: FSMContext):
    email = msg.text.strip()
    await state.update_data(email=email)

    await msg.answer("Digite agora a *senha* da conta:")
    await state.set_state(AddStockState.waiting_senha)


# ===========================
# SENHA
# ===========================
@router.message(AddStockState.waiting_senha)
async def addstock_senha(msg: types.Message, state: FSMContext):
    senha = msg.text.strip()
    await state.update_data(senha=senha)

    await msg.answer(
        "📸 Envie agora as *imagens da conta*, uma por vez.\n\n"
        "Quando terminar digite:\n`/finish`"
    )
    await state.set_state(AddStockState.waiting_images)


# ===========================
# RECEBE IMAGENS
# ===========================
@router.message(AddStockState.waiting_images, F.photo)
async def addstock_receive_img(msg: types.Message, state: FSMContext):
    file_id = msg.photo[-1].file_id

    data = await state.get_data()
    imagens = data.get("imagens", [])
    imagens.append(file_id)

    await state.update_data(imagens=imagens)

    await msg.answer("🖼 Imagem adicionada. Envie outra ou digite /finish")


# ===========================
# FINALIZA ENVIO DE IMAGENS
# ===========================
@router.message(AddStockState.waiting_images, Command("finish"))
async def addstock_finish_images(msg: types.Message, state: FSMContext):
    await msg.answer(
        "📘 Envie agora o *tutorial* da conta.\n\n"
        "Ou digite `/default` para usar o tutorial padrão."
    )
    await state.set_state(AddStockState.waiting_tutorial)


# ===========================
# TUTORIAL PADRÃO
# ===========================
@router.message(AddStockState.waiting_tutorial, Command("default"))
async def addstock_default(msg: types.Message, state: FSMContext):
    await state.update_data(tutorial=TUTORIAL_PADRAO)
    await finalize_stock(msg, state)


# ===========================
# TUTORIAL PERSONALIZADO
# ===========================
@router.message(AddStockState.waiting_tutorial)
async def addstock_custom_tutorial(msg: types.Message, state: FSMContext):
    tutorial = msg.text.strip()
    await state.update_data(tutorial=tutorial)
    await finalize_stock(msg, state)


# ===========================
# SALVAR NO BANCO
# ===========================
async def finalize_stock(msg: types.Message, state: FSMContext):
    data = await state.get_data()

    tipo = data["tipo"]
    email = data["email"]
    senha = data["senha"]
    tutorial = data["tutorial"]
    imagens = data["imagens"]

    stock = create_stock(tipo, email, senha, tutorial)
    stock_id = stock["id"]

    for fid in imagens:
        add_stock_image(stock_id, fid)

    await state.clear()

    await msg.answer(
        f"✅ *CONTA CADASTRADA COM SUCESSO*\n\n"
        f"📦 Tipo: *{tipo}*\n"
        f"📧 Email: `{email}`\n"
        f"🔐 Senha: `{senha}`\n"
        f"🖼 Imagens adicionadas: *{len(imagens)}*\n\n"
        f"🆔 ID no estoque: *{stock_id}*\n\n"
        f"Conta pronta para entrega automática! 🚀"
    )


def register_estoque_handlers(dp):
    dp.include_router(router)
