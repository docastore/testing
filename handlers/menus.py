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
from utils.texts import texto_menu_principal, texto_saldo
from config import BANNER_FILE_ID

router = Router()

# Catálogo de produtos Amazon (card de seleção)
AMAZON_TIPOS = [
    {"label": "💻 DIGITAIS / ASSINATURAS", "cb": "amz_dig", "price": 45.00},
    {"label": "📦 MIX PEDIDOS FÍSICOS", "cb": "amz_mix", "price": 110.00},
    {"label": "🏆 PRIME ATIVO + PEDIDOS FÍSICOS", "cb": "amz_prime", "price": 125.00},
    {"label": "🔟 +10 PEDIDOS FÍSICOS", "cb": "amz_10p", "price": 155.00},
]


# ===========================
# VOLTAR → MENU PRINCIPAL
# ===========================
@router.callback_query(F.data == "menu_voltar")
async def menu_voltar(callback: types.CallbackQuery):
    """
    Voltar padrão: volta para o menu principal (mesma mensagem).
    """
    user = get_or_create_user(callback.from_user.id)
    first = callback.from_user.first_name or "Cliente"
    caption = texto_menu_principal(user, first)

    try:
        await safe_edit_caption_or_text(
            callback,
            text=caption,
            reply_markup=kb_menu_principal(),
        )
    except TelegramBadRequest:
        # fallback: se por algum motivo não der pra editar, manda um card novo
        await callback.message.answer_photo(
            photo=BANNER_FILE_ID,
            caption=caption,
            reply_markup=kb_menu_principal(),
        )

    await callback.answer()


# ===========================
# MENU AMAZON
# ===========================
@router.callback_query(F.data == "menu_amazon")
async def menu_amazon(callback: types.CallbackQuery):
    caption = "🛒 AMAZON\n\nSelecione o tipo de conta:"

    try:
        await safe_edit_caption_or_text(
            callback,
            text=caption,
            reply_markup=kb_amazon_tipos(AMAZON_TIPOS),
        )
    except TelegramBadRequest:
        await callback.message.answer(
            caption,
            reply_markup=kb_amazon_tipos(AMAZON_TIPOS),
        )

    await callback.answer()


# ===========================
# MENU SALDO
# ===========================
@router.callback_query(F.data == "menu_saldo")
async def menu_saldo(callback: types.CallbackQuery):
    user = get_or_create_user(callback.from_user.id)
    bonus = get_bonus_percent()
    caption = texto_saldo(user, bonus)

    try:
        await safe_edit_caption_or_text(
            callback,
            text=caption,
            reply_markup=kb_saldo(),
        )
    except TelegramBadRequest:
        await callback.message.answer_photo(
            BANNER_FILE_ID,
            caption=caption,
            reply_markup=kb_saldo(),
        )

    await callback.answer()


# ===========================
# PERFIL
# ===========================
@router.callback_query(F.data == "menu_perfil")
async def menu_perfil(callback: types.CallbackQuery):
    user = get_or_create_user(callback.from_user.id)

    caption = f"""
👤 Seu Perfil

🧾 DOC-ID: {user['doc_code']}
💰 Saldo: R$ {user['saldo']:.2f}
💎 Pontos: R$ {user['pontos']:.2f}

Use o menu abaixo para navegar.
""".strip()

    try:
        await safe_edit_caption_or_text(
            callback,
            text=caption,
            reply_markup=kb_menu_principal(),
        )
    except TelegramBadRequest:
        await callback.message.answer(
            caption,
            reply_markup=kb_menu_principal(),
        )

    await callback.answer()


# ===========================
# MINHAS COMPRAS – ABERTURA
# ===========================
@router.callback_query(F.data == "menu_meus_pedidos")
async def menu_meus_pedidos(callback: types.CallbackQuery):
    user = get_or_create_user(callback.from_user.id)
    await _mostrar_pedidos_pagina(callback, user_id=user["id"], page=1)


async def _mostrar_pedidos_pagina(callback: types.CallbackQuery, user_id: int, page: int):
    """
    Mostra a lista de compras na MESMA mensagem (card).
    Nada de mensagem extra com texto solto.
    """
    per_page = 5
    total = count_user_orders(user_id)
    pedidos = get_user_orders_page(user_id, page, per_page)

    if not pedidos:
        caption = "🧾 Minhas compras\n\nVocê ainda não tem compras registradas."
    else:
        caption = "🧾 Minhas compras\n\n"
        for ped in pedidos:
            caption += (
                f"• #{ped['id']} – {ped['tipo_label']} – "
                f"R$ {ped['price']:.2f} – {ped['created_at']}\n"
            )
        total_pages = (total + per_page - 1) // per_page
        caption += f"\nPágina {page} de {total_pages}"

    # Botões de paginação + voltar
    buttons = []
    nav_row = []

    if total > 0:
        total_pages = (total + per_page - 1) // per_page
        if page > 1:
            nav_row.append(
                types.InlineKeyboardButton(
                    text="⬅ Anterior",
                    callback_data=f"pedidos_page_{page - 1}",
                )
            )
        if page < total_pages:
            nav_row.append(
                types.InlineKeyboardButton(
                    text="Próxima ➡",
                    callback_data=f"pedidos_page_{page + 1}",
                )
            )
        if nav_row:
            buttons.append(nav_row)

    buttons.append(
        [types.InlineKeyboardButton(text="⬅ Voltar", callback_data="menu_voltar")]
    )

    markup = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await safe_edit_caption_or_text(
            callback,
            text=caption,
            reply_markup=markup,
        )
    except TelegramBadRequest:
        # fallback se der algum pau bizarro
        await callback.message.answer(caption, reply_markup=markup)

    await callback.answer()


@router.callback_query(F.data.startswith("pedidos_page_"))
async def menu_meus_pedidos_page(callback: types.CallbackQuery):
    try:
        page = int(callback.data.split("_")[-1])
    except ValueError:
        await callback.answer("Página inválida.", show_alert=True)
        return

    user = get_or_create_user(callback.from_user.id)
    await _mostrar_pedidos_pagina(callback, user_id=user["id"], page=page)


# ===========================
# DETALHES DE UM PEDIDO
# ===========================
@router.callback_query(F.data.startswith("pedido_"))
async def detalhes_pedido(callback: types.CallbackQuery):
    """
    Se você quiser depois, dá pra colocar um botão "ver detalhes"
    em cada linha da lista. Por enquanto, deixo o handler preparado.
    """
    try:
        pedido_id = int(callback.data.split("_")[1])
    except (IndexError, ValueError):
        await callback.answer("ID de pedido inválido.", show_alert=True)
        return

    pedido = get_order_details(pedido_id)
    if not pedido:
        await callback.answer("Pedido não encontrado.", show_alert=True)
        return

    stock_item = get_full_stock_by_id(pedido["stock_id"])
    if not stock_item:
        await callback.answer("Conta não encontrada.", show_alert=True)
        return

    email = stock_item["email"]
    senha = stock_item["senha"]
    tutorial = stock_item["tutorial"]
    imagens = stock_item["imagens"]

    caption = f"""
📄 Pedido #{pedido_id}

📦 {pedido['tipo_label']}
💰 Valor: R$ {pedido['price']:.2f}
📅 {pedido['created_at']}

🔑 SEUS ACESSOS
{email}
{senha}

📘 Tutorial:
{tutorial or "Nenhum tutorial cadastrado."}
""".strip()

    # Mostra os detalhes na mesma mensagem de texto
    await safe_edit_caption_or_text(
        callback,
        text=caption,
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="⬅ Voltar para compras",
                        callback_data="menu_meus_pedidos",
                    )
                ]
            ]
        ),
    )

    # Se tiver imagens, manda em seguida (essas podem ficar como mensagens extras mesmo)
    for fid in imagens:
        await callback.message.answer_photo(fid)

    await callback.answer()


# ===========================
# NOVIDADES
# ===========================
@router.callback_query(F.data == "menu_novidades")
async def menu_novidades(callback: types.CallbackQuery):
    caption = """
📢 Novidades & Cupons

Por enquanto ainda não temos novidades ativas.
Fique de olho aqui que em breve vou lançar cupons, promoções e bônus de recarga. 🔥
""".strip()

    try:
        await safe_edit_caption_or_text(
            callback,
            text=caption,
            reply_markup=kb_menu_principal(),
        )
    except TelegramBadRequest:
        await callback.message.answer(
            caption,
            reply_markup=kb_menu_principal(),
        )

    await callback.answer()


# ===========================
# SUPORTE
# ===========================
@router.callback_query(F.data == "menu_suporte")
async def menu_suporte(callback: types.CallbackQuery):
    caption = """
🎫 Suporte

Para suporte, responda essa mensagem ou chame no WhatsApp
que vamos te atender o mais rápido possível. 💬
""".strip()

    try:
        await safe_edit_caption_or_text(
            callback,
            text=caption,
            reply_markup=kb_menu_principal(),
        )
    except TelegramBadRequest:
        await callback.message.answer(
            caption,
            reply_markup=kb_menu_principal(),
        )

    await callback.answer()


# ===========================
# VOLTAR AO MENU INICIAL
# (MSG PAGAMENTO APROVADO)
# ===========================
@router.callback_query(F.data == "voltar_menu_inicial")
async def voltar_menu_inicial(callback: types.CallbackQuery):
    """
    Usado na tela de pagamento aprovado:
    - apaga a mensagem atual
    - manda um novo card igual ao /start.
    """
    try:
        await callback.message.delete()
    except Exception:
        pass

    user = get_or_create_user(callback.from_user.id)
    first = callback.from_user.first_name or "Cliente"
    caption = texto_menu_principal(user, first)

    await callback.message.answer_photo(
        photo=BANNER_FILE_ID,
        caption=caption,
        reply_markup=kb_menu_principal(),
    )

    await callback.answer()


# ===========================
# HELPER: EDITAR CAPTION/TEXTO
# ===========================
async def safe_edit_caption_or_text(
    callback: types.CallbackQuery,
    text: str,
    reply_markup=None,
):
    """
    Se a msg tem foto -> edit_caption.
    Se não tem -> edit_text.
    Evita erro "no caption in the message to edit".
    """
    msg = callback.message
    if msg.photo:
        return await msg.edit_caption(text, reply_markup=reply_markup)
    else:
        return await msg.edit_text(text, reply_markup=reply_markup)


# ===========================
# REGISTRO NO DISPATCHER
# ===========================
def register_menu_handlers(dp):
    dp.include_router(router)
