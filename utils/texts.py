from config import BANNER_FILE_ID


# ===== TUTORIAL PADRÃO DAS CONTAS ENTREGUES =====

TUTORIAL_PADRAO = """
📘 *TUTORIAL DE USO DA CONTA*

1. Não alterar nenhum dado da conta (senha, nome, telefone, e-mail).
2. Não adicionar cartões, formas de pagamento ou endereços.
3. Sempre utilizar *navegação anônima* para logar.
4. Não usar o aplicativo — apenas navegador.
5. Não tente alterar nenhum dado no perfil.
6. Faça login e aguarde 30 segundos antes de navegar.
7. Caso algo dê errado, não mexa em nada: chame o suporte.
"""


# ===== TEXTOS DO MENU PRINCIPAL =====

def texto_menu_principal(user, first_name):
    return f"""
⭐ Olá *{first_name}*, bem-vindo à *DOCA STORE*! 😈

A melhor loja de contas Amazon com aprovação real e estoque verificado.

👤 *Seu Perfil:*
🆔 Telegram: `{user['telegram_id']}`
🧾 DOC-ID: *{user['doc_code']}*
💰 Saldo: R$ {user['saldo']:.2f}
💎 Pontos: R$ {user['pontos']:.2f}

Escolha uma opção abaixo:
"""


# ===== TEXTO SALDO =====

def texto_saldo(user, bonus):
    if bonus > 0:
        bonus_txt = f"✨ Promoção ativa: *bônus de {bonus:.0f}%* em recargas!"
    else:
        bonus_txt = "Nenhuma promoção ativa no momento."

    return f"""
💰 *Seu saldo atual:*

🧾 DOC-ID: *{user['doc_code']}*
💰 Saldo: R$ {user['saldo']:.2f}
💎 Pontos: R$ {user['pontos']:.2f}

{bonus_txt}

Clique em *Fazer recarga* para recarregar sua carteira de forma rápida.
"""


# ===== TEXTO TIPO DE CONTA =====

def texto_compra_tipo(tipo):
    return f"""
🛒 *{tipo['label']}*

💰 Preço: R$ {tipo['price']:.2f}

Pagamento via *saldo* disponível no bot.

Clique em *Comprar* para gerar seu pedido.
"""


# ===== TEXTO COMPRA SUCESSO =====

def texto_compra_sucesso(order, user):
    return f"""
✅ *COMPRA APROVADA!*

🧾 Pedido: `#{order['id']}`
🧾 DOC-ID: *{user['doc_code']}*

🛒 Produto: *{order['tipo_label']}*
💳 Valor debitado: *R$ {order['price']:.2f}*

💰 Seu saldo atual: *R$ {order['saldo_atual']:.2f}*

A conta será entregue a seguir. 🚀
"""


# ===== TEXTO SALDO INSUFICIENTE =====

def texto_saldo_insuficiente(user, tipo):
    faltam = max(0, tipo["price"] - user["saldo"])
    return f"""
❌ *SALDO INSUFICIENTE*

🛒 Produto: *{tipo['label']}*
💰 Preço: R$ {tipo['price']:.2f}
💳 Seu saldo: R$ {user['saldo']:.2f}

🔻 Faltam: R$ {faltam:.2f}

Faça uma recarga e tente novamente.
"""


# ===== ENTREGA DA CONTA =====

def texto_entrega_conta(stock):
    return f"""
🎁 *ENTREGA DA CONTA — {stock['tipo']}*

email: `{stock['email']}`
senha: `{stock['senha']}`

📘 *Tutorial:*
{stock['tutorial']}
"""
