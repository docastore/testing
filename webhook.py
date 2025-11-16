from fastapi import FastAPI, Request
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
import mercadopago

from config import MP_ACCESS_TOKEN, ADMINS_GROUP_ID, BOT_TOKEN
from models.users import (
    get_user_by_doc_code,
    get_bonus_percent,
    add_balance_by_doc,
    get_last_recharge_by_doc,
)
from models.mp_payments import mark_payment_if_new
from utils.keyboards import kb_pagamento_aprovado

app = FastAPI()
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML"),
)


@app.post("/mp/webhook")
async def mp_webhook(request: Request):
    # Log bruto da query e body
    query_params = dict(request.query_params)
    print(f"[MP][WEBHOOK] QUERY: {query_params}")

    body = await request.json()
    print(f"[MP][WEBHOOK] BODY: {body}")

    # MP pode mandar dois formatos: 'id/topic' ou 'data.id/type'
    payment_id = None
    if "id" in query_params and "topic" in query_params:
        payment_id = query_params.get("id")
    elif "data.id" in query_params and "type" in query_params:
        payment_id = query_params.get("data.id")
    elif "data" in body and isinstance(body["data"], dict) and "id" in body["data"]:
        payment_id = body["data"]["id"]

    if not payment_id:
        print("[MP][WEBHOOK] Nenhum payment_id encontrado.")
        return {"status": "ignored"}

    print(f"[MP][WEBHOOK] payment_id={payment_id}")

    # Busca detalhes do pagamento
    payment_info = sdk.payment().get(payment_id)
    if payment_info.get("status") != 200:
        print("[MP][WEBHOOK] Erro ao buscar pagamento:", payment_info)
        return {"status": "error"}

    p = payment_info["response"]
    status = p.get("status")
    status_detail = p.get("status_detail")
    external_reference = p.get("external_reference")  # DOC-00001
    transaction_amount = float(p.get("transaction_amount", 0))

    print(f"[MP][WEBHOOK] status={status} status_detail={status_detail}")
    print(
        f"[MP][WEBHOOK] Pagamento APROVADO. DOC={external_reference} "
        f"valor={transaction_amount:.2f}"
    )

    # Só processa se aprovado de fato
    if status != "approved" or status_detail != "accredited":
        print(f"[MP][WEBHOOK] Pagamento ainda não aprovado. Status: {status}")
        return {"status": "pending"}

    # Evita processar o MESMO pagamento mais de uma vez
    if not mark_payment_if_new(
        payment_id,
        status,
        status_detail,
        transaction_amount,
        external_reference,
    ):
        print(f"[MP][WEBHOOK] pagamento {payment_id} já processado anteriormente. Ignorando.")
        return {"status": "ignored"}

    # A partir daqui temos: pagamento aprovado E ainda não processado

    # Encontra o usuário pelo DOC
    if not external_reference:
        print("[MP][WEBHOOK] Sem external_reference (DOC). Abortando crédito.")
        return {"status": "error"}

    doc_code = external_reference  # DOC-00001
    user = get_user_by_doc_code(doc_code)
    if not user:
        print(f"[MP][WEBHOOK] Usuário não encontrado para DOC {doc_code}.")
        return {"status": "error"}

    telegram_id = user["telegram_id"]

    # Calcula bônus
    bonus_percent = get_bonus_percent(transaction_amount) or 0
    bonus_amount = (transaction_amount * bonus_percent) / 100.0
    credit_value = transaction_amount + bonus_amount

    # Aplica o crédito no saldo
    new_balance = add_balance_by_doc(doc_code, credit_value)

    print(
        f"[MP][WEBHOOK] Crédito aplicado DOC={doc_code} +R$ {credit_value:.2f} "
        f"(base={transaction_amount:.2f}, bônus={bonus_amount:.2f})"
    )

    # Notifica grupo de admins
    try:
        msg_admin = (
            "💸 Pagamento aprovado via Pix\n\n"
            f"🧾 DOC: {doc_code}\n"
            f"💰 Valor pago: R$ {transaction_amount:.2f}\n"
            f"🎁 Bônus: {bonus_percent:.0f}% (R$ {bonus_amount:.2f})\n"
            f"✅ Crédito aplicado: R$ {credit_value:.2f}\n"
            f"📊 Saldo atual: R$ {new_balance:.2f}\n"
        )
        await bot.send_message(chat_id=ADMINS_GROUP_ID, text=msg_admin)
    except Exception as e:
        print("[MP][WEBHOOK] erro ao notificar admins:", repr(e))

    # Texto padrão pro usuário
    msg_user = (
        "✅ <b>Pagamento aprovado!</b>\n\n"
        f"💰 Valor creditado: R$ {credit_value:.2f}\n"
        f"📊 Seu novo saldo: R$ {new_balance:.2f}\n\n"
        "Clique no botão abaixo para voltar ao menu inicial. 🚀"
    )

    # Notifica o usuário
    if telegram_id:
        edit_ok = False

        # 1) tenta EDITAR a mensagem do PIX se tivermos message_id salvo
        try:
            rec = get_last_recharge_by_doc(doc_code)
        except Exception as e:
            print("[MP][WEBHOOK] erro ao buscar última recarga:", repr(e))
            rec = None

        if rec and rec.get("message_id"):
            try:
                await bot.edit_message_caption(
                    chat_id=telegram_id,
                    message_id=rec["message_id"],
                    caption=msg_user,
                    reply_markup=kb_pagamento_aprovado(),
                )
                edit_ok = True
            except Exception as e:
                print("[MP][WEBHOOK] erro ao editar mensagem do PIX:", repr(e))
        else:
            print("[MP][WEBHOOK] nenhuma recarga com message_id para DOC", doc_code)

        # 2) fallback: se não conseguimos editar por qualquer motivo, manda mensagem nova
        if not edit_ok:
            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=msg_user,
                    reply_markup=kb_pagamento_aprovado(),
                )
            except Exception as e:
                print("[MP][WEBHOOK] erro ao enviar msg de aprovado ao usuário:", repr(e))

    # Resposta pro MP
    return {"status": "ok"}
