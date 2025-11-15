from aiogram import Router, types, F

from models.users import get_or_create_user
from models.orders import create_order_and_debit, link_order_to_stock
from models.stock import get_one_available_stock, mark_stock_used
from utils.keyboards import kb_amazon_tipos, kb_tipo_detalhe
from utils.texts import (
    texto_compra_tipo,
    texto_compra_sucesso,
    texto_saldo_insuficiente,
    texto_entrega_conta,
)

router = Router()

AMAZON_TIPOS = [
    {"label": "💻 DIGITAIS / ASSINATURAS", "cb": "amz_dig", "price": 45.00, "code": "AMZ_DIG"},
    {"label": "📦 MIX PEDIDOS FÍSICOS", "cb": "amz_mix", "price": 110.00, "code": "AMZ_MIX"},
    {"label": "🏆 PRIME ATIVO + PEDIDOS FÍSICOS", "cb": "amz_prime", "price": 125.00, "code": "AMZ_PRIME"},
    {"label": "🔟 +10 PEDIDOS FÍSICOS", "cb": "amz_10p", "price": 155.00, "code": "AMZ_10P"},
]


def _find_tipo(cb_value: str):
    for t in AMAZON_TIPOS:
        if t["cb"] == cb_value:
            return t
    return None


# ===========================
# MOSTRAR DETALHES DE UM TIPO
# ===========================
@router.callback_query(F.data.startswith("amz_"))
async def ver_tipo(callback: types.CallbackQuery):
    cb = callback.data
    tipo = _find_tipo(cb)

    if not tipo:
        return await callback.answer("Tipo inválido.", show_alert=True)

    caption = texto_compra_tipo(tipo)

    await callback.message.edit_caption(
        caption=caption,
        reply_markup=kb_tipo_detalhe(tipo)
    )
    await callback.answer()


# ===========================
# COMPRAR UM TIPO
# ===========================
@router.callback_query(F.data.startswith("buy_"))
async def comprar_tipo(callback: types.CallbackQuery):
    cb = callback.data.replace("buy_", "")
    tipo = _find_tipo(cb)

    if not tipo:
        return await callback.answer("Produto não encontrado.", show_alert=True)

    user = get_or_create_user(callback.from_user.id)

    # 1) Verifica estoque
    stock = get_one_available_stock(tipo["code"])
    if not stock:
        caption = (
            f"❌ *SEM ESTOQUE DISPONÍVEL*\n\n"
            f"Produto: *{tipo['label']}*\n\n"
            "No momento não há contas desse tipo cadastradas.\n"
            "Chame o suporte."
        )
        await callback.message.edit_caption(
            caption=caption,
            reply_markup=kb_amazon_tipos(AMAZON_TIPOS)
        )
        return await callback.answer("Sem estoque disponível.")

    # 2) Verifica saldo
    if user["saldo"] < tipo["price"]:
        caption = texto_saldo_insuficiente(user, tipo)
        await callback.message.edit_caption(
            caption=caption,
            reply_markup=kb_tipo_detalhe(tipo)
        )
        return await callback.answer("Saldo insuficiente.")

    # 3) Debita e cria pedido
    try:
        order = create_order_and_debit(
            user_id=user["id"],
            categoria="AMAZON",
            tipo_code=tipo["code"],
            tipo_label=tipo["label"],
            price=tipo["price"],
        )
    except ValueError:
        user = get_or_create_user(callback.from_user.id)
        caption = texto_saldo_insuficiente(user, tipo)
        await callback.message.edit_caption(
            caption=caption,
            reply_markup=kb_tipo_detalhe(tipo)
        )
        return await callback.answer("Saldo insuficiente.")

    # 4) Marca estoque como usado
    mark_stock_used(stock["id"])

    # 5) Vincula pedido à conta entregue
    link_order_to_stock(order["id"], stock["id"])

    # 6) Atualiza user após débito
    user = get_or_create_user(callback.from_user.id)

    # 7) Mensagem de sucesso
    caption = texto_compra_sucesso(order, user)
    await callback.message.edit_caption(
        caption=caption,
        reply_markup=kb_amazon_tipos(AMAZON_TIPOS)
    )

    # 8) Enviar conta (texto)
    stock_for_text = {**stock, "tipo": tipo["label"]}
    await callback.message.answer(texto_entrega_conta(stock_for_text))

    # 9) Envia imagens (se houver)
    imagens = stock.get("imagens", [])
    if imagens:
        media = [types.InputMediaPhoto(media=fid) for fid in imagens]
        await callback.message.answer_media_group(media)

    await callback.answer("Compra concluída. Conta entregue. ✅")


def register_compras_handlers(dp):
    dp.include_router(router)
