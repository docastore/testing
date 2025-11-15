from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ===== MENU PRINCIPAL =====

def kb_menu_principal():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Comprar contas Amazon", callback_data="menu_amazon")],
        [
            InlineKeyboardButton(text="💰 Saldo", callback_data="menu_saldo"),
            InlineKeyboardButton(text="👤 Meu perfil", callback_data="menu_perfil"),
        ],
        [InlineKeyboardButton(text="🧾 Minhas compras", callback_data="menu_meus_pedidos")],
        [InlineKeyboardButton(text="📢 Novidades & Cupons", callback_data="menu_novidades")],
        [
            InlineKeyboardButton(text="🎫 Suporte", callback_data="menu_suporte"),
            InlineKeyboardButton(text="📣 Grupo aberto", callback_data="menu_grupo"),
        ],
    ])


# ===== TIPOS DE CONTA AMAZON =====

def kb_amazon_tipos(tipos):
    lista = []
    for t in tipos:
        lista.append([InlineKeyboardButton(text=t["label"], callback_data=t["cb"])])

    lista.append([InlineKeyboardButton(text="⬅️ Voltar", callback_data="menu_voltar")])
    return InlineKeyboardMarkup(inline_keyboard=lista)


# ===== INFO DE UM TIPO =====

def kb_tipo_detalhe(tipo):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🛒 Comprar por R$ {tipo['price']:.2f}",
            callback_data=f"buy_{tipo['cb']}"
        )],
        [InlineKeyboardButton(text="⬅️ Voltar", callback_data="menu_amazon")],
    ])


# ===== SALDO =====

def kb_saldo():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Fazer recarga", callback_data="saldo_recarregar")],
        [InlineKeyboardButton(text="⬅️ Voltar", callback_data="menu_voltar")],
    ])


# ===== OPÇÕES DE RECARGA =====

def kb_recarga_opcoes():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="R$ 25", callback_data="recar_25"),
            InlineKeyboardButton(text="R$ 50", callback_data="recar_50"),
        ],
        [
            InlineKeyboardButton(text="R$ 100", callback_data="recar_100"),
            InlineKeyboardButton(text="R$ 200", callback_data="recar_200"),
        ],
        [InlineKeyboardButton(text="⬅️ Voltar", callback_data="menu_saldo")],
    ])
