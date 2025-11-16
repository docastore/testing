from aiogram import Router, types, F
from aiogram.types import BufferedInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

import base64
import mercadopago

from config import MP_ACCESS_TOKEN
from models.users import (
    get_or_create_user,
    get_bonus_percent,
    create_recharge,
    update_recharge_message_id,
)
from utils.keyboards import kb_saldo
from states.recharge_state import RechargeState

router = Router()

# ===========================
# SDK Mercado Pago
# ===========================
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)


def gerar_pix(doc_code: str, valor: float):
    """
    Cria um pagamento PIX no Mercado Pago e retorna
    o código copia-e-cola, o base64 da imagem do QR e o ticket_url.
    """
    body = {
        "transaction_amount": float(valor),
        "description": f"Recarga DocaStoreBot - R$ {valor}",
        "payment_method_id": "pix",
        "payer": {"email": "cliente@docastore.com"},
        "external_reference": doc_code,
        # URL pública do webhook (/mp/webhook)
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
async def saldo_recarregar(callback: types.CallbackQuery, state: FSMContext):
    """
    Mostra a tela onde o usuário DIGITA o valor da recarga.
    Tudo em cima da MESMA mensagem do menu saldo.
    """
    bonus = get_bonus_percent()

    if bonus > 0:
        if bonus == 100:
            bonus_txt = "✨ Promoção ativa: *recarga em dobro* (bônus de 100%)."
        else:
            bonus_txt = f"✨ Promoção ativa: *bônus de {bonus:.0f}%* em todas as recargas."
    else:
        bonus_txt = "No momento não há bônus ativo nas recargas."

    caption = f"""
💸 *Recarga via Pix automático*

{bonus_txt}

Digite o valor que você quer adicionar de saldo:

• Ex: `25`  (R$ 25,00)
• Ex: `37,50` ou `37.50`

Depois de enviar o valor, o bot vai gerar um *PIX Copia e Cola* e um QR Code.

Se quiser cancelar, é só clicar em *Voltar* abaixo.
""".strip()

    # mantém o padrão: mesma imagem, legenda nova, botões embaixo
    try:
        await callback.message.edit_caption(
            caption=caption,
            reply_markup=kb_saldo(),
        )
    except TelegramBadRequest as e:
        # se for "message is not modified", ignoramos (usuário clicou de novo no mesmo botão)
        if "message is not modified" in str(e):
            pass
        else:
            raise

    # guarda qual é a mensagem "principal" que vamos editar depois
    await state.update_data(
        menu_message_id=callback.message.message_id,
        chat_id=callback.message.chat.id,
    )

    await state.set_state(RechargeState.waiting_amount)
    await callback.answer()


# ===========================
# USUÁRIO DIGITA O VALOR
# ===========================
@router.message(RechargeState.waiting_amount)
async def processar_valor_digitado(msg: types.Message, state: FSMContext):
    texto = (msg.text or "").strip()

    # normaliza: tira "R$", espaços, troca vírgula por ponto
    texto_clean = (
        texto.replace("R$", "")
        .replace("r$", "")
        .replace(" ", "")
        .replace(",", ".")
    )

    try:
        valor = float(texto_clean)
    except ValueError:
        await msg.answer(
            "❌ Não entendi o valor.\n\n"
            "Manda só o número, por exemplo:\n"
            "`25` ou `37.50`.",
        )
        return

    if valor <= 0:
        await msg.answer("❌ Valor inválido. Digite um valor maior que zero.")
        return

    if valor < 5:
        await msg.answer("⚠️ O valor mínimo de recarga é R$ 5,00.")
        return

    # recupera dados do estado: qual mensagem vamos editar
    data = await state.get_data()
    menu_message_id = data.get("menu_message_id")
    chat_id = data.get("chat_id") or msg.chat.id

    # 1) Garante que o usuário existe
    user = get_or_create_user(msg.from_user.id)

    # 2) Cria o registro da recarga
    try:
        rec = create_recharge(user["id"], valor)
    except Exception as e:
        print("[BOT] Erro ao criar recarga:", e)
        await msg.answer("❌ Não foi possível registrar a recarga. Tente novamente mais tarde.")
        await state.clear()
        return

    # 3) Gera o PIX
    try:
        pix = gerar_pix(user["doc_code"], valor)
    except Exception as e:
        print("[MP] Erro ao gerar PIX:", e)
        await msg.answer(
            "❌ Não foi possível gerar o PIX agora. "
            "Tente novamente mais tarde."
        )
        await state.clear()
        return

    bonus_txt = (
        f"{rec['bonus_percent']:.0f}% ( + R$ {rec['bonus_amount']:.2f} )"
        if rec["bonus_percent"] > 0
        else "0%"
    )

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
""".strip()

    # tenta manter o fluxo em UMA mensagem:
    try:
        img_bytes = base64.b64decode(pix["qr_base64"])
        photo = BufferedInputFile(img_bytes, filename="qrcode_pix.png")

        # 1) troca a foto pela do QR
        await msg.bot.edit_message_media(
            chat_id=chat_id,
            message_id=menu_message_id,
            media=InputMediaPhoto(media=photo),
        )

        # 2) troca a legenda da mesma mensagem
        await msg.bot.edit_message_caption(
            chat_id=chat_id,
            message_id=menu_message_id,
            caption=caption,
            reply_markup=kb_saldo(),
        )

        # 3) salva o message_id na recarga para o webhook editar depois
        try:
            update_recharge_message_id(rec["id"], menu_message_id)
        except Exception as e:
            print("[BOT] Erro ao salvar message_id da recarga:", e)

    except Exception as e:
        # fallback: se der ruim pra editar a mídia, manda mensagem nova (não é o ideal, mas não quebra)
        print("[BOT] Erro ao editar mensagem principal com QR:", e)
        try:
            img_bytes = base64.b64decode(pix["qr_base64"])
            photo = BufferedInputFile(img_bytes, filename="qrcode_pix.png")

            env = await msg.answer_photo(
                photo=photo,
                caption=caption,
                reply_markup=kb_saldo(),
            )
            update_recharge_message_id(rec["id"], env.message_id)
        except Exception as e2:
            print("[BOT] Erro no fallback do QR:", e2)
            await msg.answer(
                caption,
                reply_markup=kb_saldo(),
            )

    # apaga a mensagem do valor digitado pra deixar o chat clean
    try:
        await msg.delete()
    except Exception:
        pass

    await state.clear()


def register_saldo_handlers(dp):
    """
    Registra todas as rotas de saldo no Dispatcher principal.
    O main.py faz: register_saldo_handlers(dp)
    """
    dp.include_router(router)
