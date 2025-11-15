from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest

from models.users import get_or_create_user, get_bonus_percent
from models.orders import (
    get_user_orders_page,
    count_user_orders,
    get_order_details,
)
from models.stock import get_full_stock_by_id

from utils.keyboards import (
    kb_menu_principal,
    kb_amazon_tipos,
    kb_saldo,
)
from utils.texts import texto_menu_principal
from config import BANNER_FILE_ID


router = Router()

# Catálogo de produtos Amazon
AMAZON_TIPOS = [
    {"label": "💻 DIGITAIS / ASSINATURAS", "cb": "amz_dig", "price": 45.00},
    {"label": "📦 MIX PEDIDOS FÍSICOS", "cb": "amz_mix", "price": 110.00},
    {"label": "🏆 PRIME ATIVO + PEDIDOS FÍSICOS", "cb": "amz_prime", "price": 125.00},
    {"label": "🔟 +10 PEDIDOS FÍSICOS", "cb": "amz_10p", "price": 155.00},
]


# ===========================
# VOLTAR AO MENU PRINCIPAL
# ===========================
@router.callback_query(F.data == "menu_voltar")
async def menu_voltar(callback: types.CallbackQuery):
    user = get_or_create_user(callback.from_user.id)
    caption = texto_menu_principal(user, callback.from_user.first_name)


    try:
        # Se a mensagem atual tem foto, usamos caption
        if callback.message.photo:
            await callback.message.edit_caption(
                caption=caption,
                reply_markup=kb_menu_principal()
            )
        else:
            # Se for texto puro, usamos edit_text
            await callback.message.edit_text(
                text=caption,
                reply_markup=kb_menu_principal()
            )
    except TelegramBadRequest:
        # Se não der pra editar (ex: mensagem de sistema, sem caption, etc),
        # mandamos um novo "card" da loja com a foto padrão
        await callback.message.answer_photo(
            BANNER_FILE_ID,
            caption=caption,
            reply_markup=kb_menu_principal()
        )

    await callback.answer()



# ===========================
# MENU AMAZON
# ===========================
@router.callback_query(F.data == "menu_amazon")
async def menu_amazon(callback: types.CallbackQuery):
    caption = "🛒 *AMAZON*\n\nSelecione o tipo de conta:"
    await callback.message.edit_caption(
        caption=caption,
        reply_markup=kb_amazon_tipos(AMAZON_TIPOS)
    )
    await callback.answer()


# ===========================
# MENU SALDO
# ===========================
@router.callback_query(F.data == "menu_saldo")
async def menu_saldo(callback: types.CallbackQuery):
    user = get_or_create_user(callback.from_user.id)
    bonus = get_bonus_percent()

    from utils.texts import texto_saldo
    caption = texto_saldo(user, bonus)

    await callback.message.edit_caption(
        caption=caption,
        reply_markup=kb_saldo()
    )
    await callback.answer()


# ===========================
# MENU PERFIL
# ===========================
@router.callback_query(F.data == "menu_perfil")
async def menu_perfil(callback: types.CallbackQuery):
    user = get_or_create_user(callback.from_user.id)

    caption = f"""
👤 *Seu Perfil*

🧾 DOC-ID: *{user['doc_code']}*
💰 Saldo: R$ {user['saldo']:.2f}
💎 Pontos: R$ {user['pontos']:.2f}
"""

    await callback.message.edit_caption(
        caption=caption,
        reply_markup=kb_menu_principal()
    )
    await callback.answer()


# ===========================
# MENU NOVIDADES
# ===========================
@router.callback_query(F.data == "menu_novidades")
async def menu_novidades(callback: types.CallbackQuery):
    caption = """
📢 *NOVIDADES & CUPONS*

Aqui você receberá avisos de novas contas, cupons e promoções.
Fique ligado! 🔥
"""

    await callback.message.edit_caption(
        caption=caption,
        reply_markup=kb_menu_principal()
    )
    await callback.answer()


# ===========================
# MENU SUPORTE
# ===========================
@router.callback_query(F.data == "menu_suporte")
async def menu_suporte(callback: types.CallbackQuery):
    caption = """
🎫 *SUPORTE*

Em breve o sistema de tickets estará disponível diretamente no bot.
"""

    await callback.message.edit_caption(
        caption=caption,
        reply_markup=kb_menu_principal()
    )
    await callback.answer()


# ===========================
# MENU GRUPO
# ===========================
@router.callback_query(F.data == "menu_grupo")
async def menu_grupo(callback: types.CallbackQuery):
    caption = """
📣 *GRUPO ABERTO — DOCA STORE*

O link oficial será adicionado em breve. 🚀
"""

    await callback.message.edit_caption(
        caption=caption,
        reply_markup=kb_menu_principal()
    )
    await callback.answer()


def register_menu_handlers(dp):
    dp.include_router(router)

# ====== MINHAS COMPRAS (PÁGINA 1) ======
@router.callback_query(F.data == "menu_meus_pedidos")
async def menu_meus_pedidos(callback: types.CallbackQuery):
    user = get_or_create_user(callback.from_user.id)
    await _mostrar_pedidos_pagina(callback.message, user["id"], page=1)
    await callback.answer()


# ====== TROCAR PÁGINA (meusped_X) ======
@router.callback_query(F.data.startswith("meusped_"))
async def menu_meus_pedidos_paginado(callback: types.CallbackQuery):
    user = get_or_create_user(callback.from_user.id)
    try:
        page = int(callback.data.replace("meusped_", ""))
    except ValueError:
        page = 1

    await _mostrar_pedidos_pagina(callback.message, user["id"], page=page)
    await callback.answer()


async def _mostrar_pedidos_pagina(message: types.Message, user_id: int, page: int):
    page_size = 5
    total = count_user_orders(user_id)
    if total == 0:
        caption = """
🧾 *MINHAS COMPRAS*

Você ainda não realizou nenhuma compra.
        """
        await message.edit_caption(
            caption=caption,
            reply_markup=kb_menu_principal()
        )
        return

    total_pages = (total + page_size - 1) // page_size
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    orders = get_user_orders_page(user_id, page, page_size)

    linhas = []
    for o in orders:
        linhas.append(
            f"• `#{o['id']}` — *{o['tipo_label']}* — R$ {o['price']:.2f} — {o['created_at']}"
        )

    linhas_texto = "\n".join(linhas)

    caption = (
        f"🧾 *MINHAS COMPRAS* (página {page}/{total_pages})\n\n"
        f"{linhas_texto}\n\n"
        f"Clique em um pedido abaixo para ver a conta novamente:"
    )

    buttons = []
    for o in orders:
        buttons.append([
            types.InlineKeyboardButton(
                text=f"📄 Pedido #{o['id']} – {o['tipo_label']}",
                callback_data=f"verpedido_{o['id']}"
            )
        ])

    nav_row = []
    if page > 1:
        nav_row.append(
            types.InlineKeyboardButton(
                text="⬅ Página anterior",
                callback_data=f"meusped_{page-1}",
            )
        )
    if page < total_pages:
        nav_row.append(
            types.InlineKeyboardButton(
                text="Próxima página ➡",
                callback_data=f"meusped_{page+1}",
            )
        )

    if nav_row:
        buttons.append(nav_row)

    buttons.append([
        types.InlineKeyboardButton(text="⬅ Voltar", callback_data="menu_voltar")
    ])

    markup = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.edit_caption(
        caption=caption,
        reply_markup=markup
    )



# ====== VER UMA COMPRA ESPECÍFICA (REEXIBIR CONTA) ======
@router.callback_query(F.data.startswith("verpedido_"))
async def menu_ver_pedido(callback: types.CallbackQuery):
    pedido_id = int(callback.data.replace("verpedido_", ""))

    user = get_or_create_user(callback.from_user.id)
    user_id = user["id"]

    pedido = get_order_details(pedido_id, user_id)
    if pedido is None:
        return await callback.answer("❌ Pedido não encontrado.", show_alert=True)

    stock_id = pedido["stock_id"]
    if stock_id is None:
        return await callback.answer(
            "❌ Este pedido é antigo e não possui vínculo com uma conta específica.",
            show_alert=True,
        )

    conta = get_full_stock_by_id(stock_id)
    if not conta:
        return await callback.answer("❌ Conta não encontrada.", show_alert=True)

    email = conta["email"]
    senha = conta["senha"]
    tutorial = conta["tutorial"]
    imagens = conta["imagens"]

    caption = f"""
📄 *Pedido #{pedido_id}*

📦 *{pedido['tipo_label']}*
💰 Valor: R$ {pedido['price']:.2f}
📅 {pedido['created_at']}

🔑 *SEUS ACESSOS*
`{email}`
`{senha}`

📘 *TUTORIAL*
{tutorial}
"""

    await callback.message.edit_caption(
        caption=caption,
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="⬅ Voltar", callback_data="menu_meus_pedidos")]
            ]
        )
    )

    for fid in imagens:
        await callback.message.answer_photo(fid)

    await callback.answer()
