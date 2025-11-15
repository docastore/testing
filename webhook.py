from fastapi import FastAPI, Request
import mercadopago

from config import MP_ACCESS_TOKEN, ADMINS_GROUP_ID, BOT_TOKEN
from models.users import get_user_by_doc_code, get_bonus_percent, add_balance_by_doc
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

app = FastAPI()
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
bot = Bot(BOT_TOKEN, parse_mode="HTML")


@app.post("/mp/webhook")
async def mp_webhook(request: Request):
    # --- Logs básicos ---
    query = dict(request.query_params)
    body = await request.json()

    print("[MP][WEBHOOK] QUERY:", query)
    print("[MP][WEBHOOK] BODY:", body)

    # --- Descobrir o payment_id (MP manda 2 formatos possíveis) ---
    payment_id = None

    # Formato novo: /mp/webhook?data.id=123&type=payment
    if query.get("type") == "payment" and "data.id" in query:
        payment_id = query["data.id"]

    # Formato antigo: /mp/webhook?id=123&topic=payment
    elif query.get("topic") == "payment" and "id" in query:
        payment_id = query["id"]

    if not payment_id:
        print("[MP][WEBHOOK] sem payment_id na query, ignorando.")
        return {"status": "ok"}

    print(f"[MP][WEBHOOK] payment_id detectado: {payment_id}")

    # --- Buscar detalhes do pagamento no Mercado Pago ---
    try:
        mp_resp = sdk.payment().get(payment_id)
        payment = mp_resp.get("response", {}) or {}
        print("[MP][WEBHOOK] RESPONSE:", payment)
    except Exception as e:
        print("[MP][WEBHOOK] erro ao consultar pagamento:", repr(e))
        return {"status": "error"}

    # --- Agora SIM podemos ler status ---
    status = payment.get("status")
    status_detail = payment.get("status_detail")
    print(f"[MP][WEBHOOK] status={status} status_detail={status_detail}")

    # Se ainda não aprovou, só loga e sai
    if status != "approved":
        print(f"[MP][WEBHOOK] Pagamento ainda não aprovado. Status: {status}")
        return {"status": "ok"}

    # --- Pagamento aprovado: extrair infos principais ---
    transaction_amount = float(payment.get("transaction_amount", 0) or 0)
    external_reference = payment.get("external_reference") or ""
    payer_info = payment.get("payer") or {}
    payer_email = payer_info.get("email")
    doc_code = external_reference  # DOC-00001, DOC-00002, etc.

    print(
        f"[MP][WEBHOOK] Pagamento APROVADO. DOC={doc_code} "
        f"valor={transaction_amount:.2f}"
    )

    # --- Bônus ---
    bonus_percent = get_bonus_percent() or 0
    bonus_value = transaction_amount * (bonus_percent / 100)
    credit_value = transaction_amount + bonus_value

    # --- Aplica o crédito no banco ---
    try:
        add_balance_by_doc(doc_code, credit_value)
        print(
            f"[MP][WEBHOOK] Crédito aplicado DOC={doc_code} +R$ {credit_value:.2f} "
            f"(base={transaction_amount:.2f}, bônus={bonus_value:.2f})"
        )
    except Exception as e:
        print("[MP][WEBHOOK] ERRO ao aplicar crédito no banco:", repr(e))
        return {"status": "error"}

    # --- Recarrega o usuário para pegar o saldo atualizado ---
    user = get_user_by_doc_code(doc_code)
    if not user:
        print(f"[MP][WEBHOOK] Usuário não encontrado para DOC={doc_code}")
        return {"status": "ok"}

    telegram_id = user.get("telegram_id") or user.get("tg_id")
    nome = user.get("nome") or user.get("first_name") or "Cliente"

    # IMPORTANTE: usar a coluna correta do banco (provavelmente 'saldo')
    saldo_atual = float(user.get("saldo", 0) or 0)

    # --- Notificar grupo de administradores ---
    if ADMINS_GROUP_ID:
        msg_admin = (
            "💸 <b>Pagamento aprovado via Pix</b>\n\n"
            f"👤 Cliente: <code>{nome}</code>\n"
            f"🧾 DOC: <code>{doc_code}</code>\n"
            f"📧 E-mail MP: <code>{payer_email or 'não informado'}</code>\n"
            f"💰 Valor pago: R$ {transaction_amount:.2f}\n"
            f"🎁 Bônus: {bonus_percent:.0f}% (R$ {bonus_value:.2f})\n"
            f"✅ Crédito aplicado: R$ {credit_value:.2f}\n"
            f"📊 Saldo atual: R$ {saldo_atual:.2f}"
        )
        try:
            await bot.send_message(ADMINS_GROUP_ID, msg_admin)
        except Exception as e:
            print("[MP][WEBHOOK] erro ao notificar grupo ADM:", repr(e))

    # --- (Opcional) Notificar o próprio usuário no privado ---
    if telegram_id:
        msg_user = (
            "✅ <b>Pagamento aprovado!</b>\n\n"
            f"💰 Valor creditado: R$ {credit_value:.2f}\n"
            f"📊 Seu novo saldo: R$ {saldo_atual:.2f}\n\n"
            "Obrigado por recarregar na DOCA STORE BOT 🚀"
        )
        try:
            await bot.send_message(telegram_id, msg_user)
        except Exception as e:
            print("[MP][WEBHOOK] erro ao notificar usuário:", repr(e))

    return {"status": "ok"}
