from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def kb_admin_panel():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Estoque", callback_data="adm_estoque")],
        [InlineKeyboardButton(text="💳 Bônus de Recarga", callback_data="adm_bonus")],
        [InlineKeyboardButton(text="⬅ Voltar para a loja", callback_data="menu_voltar")],
    ])


def kb_admin_estoque():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Resumo de estoque", callback_data="adm_estoque_summary")],
        [InlineKeyboardButton(text="📋 Listar por tipo", callback_data="adm_estoque_list_tipos")],
        [InlineKeyboardButton(text="➕ Adicionar estoque", callback_data="adm_addstock")],
        [InlineKeyboardButton(text="⬅ Voltar painel admin", callback_data="adm_panel")],
    ])


def kb_admin_addstock_select():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💻 DIGITAIS", callback_data="adm_add_AMZ_DIG")],
        [InlineKeyboardButton(text="📦 MIX FÍSICOS", callback_data="adm_add_AMZ_MIX")],
        [InlineKeyboardButton(text="🏆 PRIME + FÍSICOS", callback_data="adm_add_AMZ_PRIME")],
        [InlineKeyboardButton(text="🔟 +10 PEDIDOS", callback_data="adm_add_AMZ_10P")],
        [InlineKeyboardButton(text="⬅ Voltar estoque", callback_data="adm_estoque")],
    ])


def kb_admin_bonus():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="0%", callback_data="adm_bonus_0"),
            InlineKeyboardButton(text="25%", callback_data="adm_bonus_25")
        ],
        [
            InlineKeyboardButton(text="50%", callback_data="adm_bonus_50"),
            InlineKeyboardButton(text="100% (DOBRO)", callback_data="adm_bonus_100")
        ],
        [InlineKeyboardButton(text="⬅ Voltar painel admin", callback_data="adm_panel")],
    ])


def kb_admin_list_tipos_para_remover():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💻 DIGITAIS", callback_data="adm_list_AMZ_DIG")],
        [InlineKeyboardButton(text="📦 MIX FÍSICOS", callback_data="adm_list_AMZ_MIX")],
        [InlineKeyboardButton(text="🏆 PRIME + FÍSICOS", callback_data="adm_list_AMZ_PRIME")],
        [InlineKeyboardButton(text="🔟 +10 PEDIDOS", callback_data="adm_list_AMZ_10P")],
        [InlineKeyboardButton(text="⬅ Voltar estoque", callback_data="adm_estoque")],
    ])
