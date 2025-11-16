from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ===== MENU PRINCIPAL =====

def kb_menu_principal() -> InlineKeyboardMarkup:
    """
    Menu principal do bot.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🛒 Comprar contas Amazon",
                callback_data="menu_amazon",
            )
        ],
        [
            InlineKeyboardButton(text="💰 Saldo", callback_data="menu_saldo"),
            InlineKeyboardButton(text="👤 Meu perfil", callback_data="menu_perfil"),
        ],
        [
            InlineKeyboardButton(
                text="🧾 Minhas compras",
                callback_data="menu_meus_pedidos",
            )
        ],
        [
            InlineKeyboardButton(
                text="📢 Novidades & Cupons",
                callback_data="menu_novidades",
            )
        ],
        [
            InlineKeyboardButton(
                text="🎫 Suporte",
                callback_data="menu_suporte",
            )
        ],
    ])


# ===== AMAZON: LISTA DE TIPOS =====

def kb_amazon_tipos(tipos) -> InlineKeyboardMarkup:
    """
    Monta a lista de tipos de contas Amazon, recebendo uma lista de dicts:
    [
      {"label": "...", "cb": "amz_dig", "price": 45.00},
      ...
    ]
    """
    linhas = []
    for t in tipos:
        linhas.append([
            InlineKeyboardButton(
                text=t["label"],
                callback_data=t["cb"],
            )
        ])

    # botão de voltar
    linhas.append([
        InlineKeyboardButton(
            text="⬅️ Voltar",
            callback_data="menu_voltar",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=linhas)


# ===== INFO DE UM TIPO (DETALHE) =====

def kb_tipo_detalhe(tipo) -> InlineKeyboardMarkup:
    """
    Teclado para o detalhe de um tipo de conta Amazon,
    com botão de comprar e botão de voltar.
    Espera um dict tipo:
      {"label": "...", "cb": "amz_dig", "price": 45.00}
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"🛒 Comprar por R$ {tipo['price']:.2f}",
                callback_data=f"buy_{tipo['cb']}",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Voltar",
                callback_data="menu_amazon",
            )
        ],
    ])


# ===== PAGAMENTO APROVADO =====

def kb_pagamento_aprovado() -> InlineKeyboardMarkup:
    """
    Teclado usado na mensagem de pagamento aprovado:
    apenas um botão que volta ao menu inicial (/start-like).
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔙 Voltar ao menu inicial",
                callback_data="voltar_menu_inicial",
            )
        ]
    ])


# ===== SALDO =====

def kb_saldo() -> InlineKeyboardMarkup:
    """
    Teclado do menu de saldo.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💸 Fazer recarga",
                callback_data="saldo_recarregar",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Voltar",
                callback_data="menu_voltar",
            )
        ],
    ])


# ===== OPÇÕES DE RECARGA (FIXAS) =====

def kb_recarga_opcoes() -> InlineKeyboardMarkup:
    """
    (Se ainda for usado em algum lugar)
    Teclado com valores fixos de recarga.
    Hoje o fluxo está com valor digitado, mas
    deixo aqui porque pode estar referenciado em algum handler antigo.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="R$ 25", callback_data="recar_25"),
            InlineKeyboardButton(text="R$ 50", callback_data="recar_50"),
        ],
        [
            InlineKeyboardButton(text="R$ 100", callback_data="recar_100"),
            InlineKeyboardButton(text="R$ 200", callback_data="recar_200"),
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Voltar",
                callback_data="menu_saldo",
            )
        ],
    ])
