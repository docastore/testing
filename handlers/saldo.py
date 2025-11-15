from aiogram import Router, types, F
from aiogram.types import BufferedInputFile

import base64
import mercadopago

from config import MP_ACCESS_TOKEN  # se você tiver MP_WEBHOOK_URL pode manter, mas não é obrigatório aqui
from models.users import get_or_create_user, get_bonus_percent, create_recharge
from utils.keyboards import kb_saldo, kb_recarga_opcoes
from utils.helpers import extract_amount

router = Router()

# ===========================
# SDK Mercado Pago
# ===========================
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)


def gerar_pix(doc_id: str, valor: float):
    """
    Cria um pagamento PIX no Mercado Pago e retorna
    o código copia-e-cola, o base64 da imagem do QR e o ticket_url.
    """
    body = {
        "transaction_amount": float(valor),
        "description": f"Recarga DocaStoreBot - R$ {valor}",
        "payment_method_id": "pix",
        "payer": {"email": "cliente@docastore.com"},
        "external_reference": doc_id,
        # Aqui você já configurou com a URL HTTPS do ngrok
        "notification_url": "https://alyssa-unvague-unceasingly.ngrok-free.dev/mp/webhook",
    }

    result = sdk.payment().create(body)
    print("[MP] Resposta create():", result)

    if result.get("status") not in (200, 201):
        raise RuntimeError(f"Erro Mercado Pago: {result}")

    trx = result["response"]["point_of_interaction"]["transaction_data"]

    return {
        "qr_code": trx["qr_code"],
        "qr_base64": trx["qr_code_base64"],
        "ticket_url": trx.get("ticket_url"),
        "payment_id": result["response"]["id"],
    }


# ===========================
# BOTÃO "FAZER RECARGA"
# ===========================
@router.callback_query(F.data == "saldo_recarregar")
async def saldo_recarregar(callback: types.CallbackQuery):
    bonus = get_bonus_percent()

    if bonus > 0:
        if bonus == 100:
            bonus_txt = "✨ Promoção ativa: *recarga em dobro* (bônus de 100%)."
        else:
            bonus_txt = f"✨ Promoção ativa: *bônus de {bonus:.0f}%* em todas as recargas."
    else:
        bonus_txt = "No momento não há bônus ativo nas recargas."

    caption = f"""
💸 *Fazer recarga*

Escolha um dos valores abaixo para gerar um pedido de recarga.

{bonus_txt}

O bot vai gerar um *PIX Copia e Cola* e um QR Code.
Assim que o pagamento for aprovado, o saldo cai automaticamente. ✅
"""

    await callback.message.edit_caption(
        caption=caption,
        reply_markup=kb_recarga_opcoes()
    )
    await callback.answer()


# ===========================
# CLIQUE EM UM VALOR DE RECARGA
# (gera PIX + cria registro da recarga)
# ===========================
@router.callback_query(F.data.startswith("recar_"))
async def processar_recarga(callback: types.CallbackQuery):
    # 1) Descobre o valor escolhido (ex: recar_25 -> 25.0)
    valor = extract_amount(callback.data)
    if valor <= 0:
        await callback.answer("Valor inválido.", show_alert=True)
        return

    # 2) Garante que o usuário existe e cria registro de recarga
    user = get_or_create_user(callback.from_user.id)
    rec = create_recharge(user["id"], valor)

    # 3) Chama o Mercado Pago para gerar o PIX
    try:
        pix = gerar_pix(user["doc_code"], valor)
    except Exception as e:
        print("[MP] Erro ao gerar PIX:", e)
        await callback.answer(
            "Não foi possível gerar o PIX agora. Tente novamente mais tarde.",
            show_alert=True
        )
        return

    bonus_txt = f"{rec['bonus_percent']:.0f}% ( + R$ {rec['bonus_amount']:.2f} )" if rec["bonus_percent"] > 0 else "0%"

    caption = f"""
✅ *Pedido de recarga criado!*

🧾 ID da recarga: `#{rec['id']}`
🧾 DOC-ID: *{user['doc_code']}*

💸 Valor da recarga: R$ {rec['amount']:.2f}
🎁 Bônus configurado: {bonus_txt}
💰 Crédito final previsto: *R$ {rec['final_credit']:.2f}*

🔎 *PIX Copia e Cola:*
`{pix['qr_code']}`

Assim que o pagamento for aprovado, seu saldo será atualizado automaticamente. 🚀
"""

    # 4) Decodifica o base64 da imagem do QR para mandar como foto
    try:
        img_bytes = base64.b64decode(pix["qr_base64"])
        photo = BufferedInputFile(img_bytes, filename="qrcode_pix.png")

        await callback.message.answer_photo(
            photo=photo,
            caption=caption,
            reply_markup=kb_saldo()
        )
    except Exception as e:
        # Se por algum motivo falhar o base64, manda só texto mesmo
        print("[BOT] Erro ao enviar imagem do QR:", e)
        await callback.message.answer(
            caption,
            reply_markup=kb_saldo()
        )

    await callback.answer("PIX gerado. Pague e aguarde a aprovação. 😉")


def register_saldo_handlers(dp):
    dp.include_router(router)
