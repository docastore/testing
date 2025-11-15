from aiogram import Router, types, F
from aiogram.filters import Command

from config import ADMINS
from models.users import total_client_saldo
from models.orders import get_total_vendas, get_total_faturado
from models.recharge import get_total_recargas
from models.stock import get_stock_summary, list_stock_by_tipo, delete_stock

from utils.keyboards_admin import (
    kb_admin_panel,
    kb_admin_estoque,
    kb_admin_addstock_select,
    kb_admin_bonus,
    kb_admin_list_tipos_para_remover,
)

router = Router()


def is_admin(uid: int) -> bool:
    return uid in ADMINS


# ===========================
# /admin → Painel principal
# ===========================
@router.message(Command("admin"))
async def admin_panel_cmd(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Você não é administrador.")

    text = await build_dashboard_text()
    await msg.answer(text, reply_markup=kb_admin_panel())


# ===========================
# Callback para voltar painel (adm_panel)
# ===========================
@router.callback_query(F.data == "adm_panel")
async def admin_panel_cb(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Você não é admin.", show_alert=True)

    text = await build_dashboard_text()
    await callback.message.edit_text(text, reply_markup=kb_admin_panel())
    await callback.answer()


async def build_dashboard_text() -> str:
    vendas = get_total_vendas()
    faturado = get_total_faturado()
    recargas = get_total_recargas()
    saldo_total = total_client_saldo()
    estoque = get_stock_summary()

    return f"""
🛠 *PAINEL ADMIN – DOCA STORE*

📊 *Resumo Geral*
• Vendas realizadas: *{vendas}*
• Total faturado: *R$ {faturado:.2f}*
• Recargas criadas: *{recargas}*
• Saldo total dos clientes: *R$ {saldo_total:.2f}*

📦 *Estoque disponível*
• DIG: {estoque['AMZ_DIG']['disp']}
• MIX: {estoque['AMZ_MIX']['disp']}
• PRIME: {estoque['AMZ_PRIME']['disp']}
• +10P: {estoque['AMZ_10P']['disp']}

Use os botões abaixo para gerenciar.
    """


# ===========================
# Menu de Estoque
# ===========================
@router.callback_query(F.data == "adm_estoque")
async def admin_estoque_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Você não é admin.", show_alert=True)

    await callback.message.edit_text(
        "📦 *GERENCIAR ESTOQUE*\n\nEscolha uma opção:",
        reply_markup=kb_admin_estoque()
    )
    await callback.answer()


# ===========================
# Resumo de estoque
# ===========================
@router.callback_query(F.data == "adm_estoque_summary")
async def admin_estoque_summary(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Você não é admin.", show_alert=True)

    summary = get_stock_summary()
    caption = (
        "📦 *ESTOQUE ATUAL*\n\n"
        f"💻 DIGITAIS: {summary['AMZ_DIG']['disp']} disponíveis\n"
        f"📦 MIX FÍSICOS: {summary['AMZ_MIX']['disp']} disponíveis\n"
        f"🏆 PRIME + FÍSICOS: {summary['AMZ_PRIME']['disp']} disponíveis\n"
        f"🔟 +10 PEDIDOS: {summary['AMZ_10P']['disp']} disponíveis\n"
    )

    await callback.message.edit_text(
        caption,
        reply_markup=kb_admin_estoque()
    )
    await callback.answer()


# ===========================
# Listar estoques por tipo (para remover)
# ===========================
@router.callback_query(F.data == "adm_estoque_list_tipos")
async def admin_estoque_list_tipos(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Você não é admin.", show_alert=True)

    await callback.message.edit_text(
        "📋 *Escolha o tipo de conta para listar/remover:*",
        reply_markup=kb_admin_list_tipos_para_remover()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_list_"))
async def admin_list_stock(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Você não é admin.", show_alert=True)

    tipo = callback.data.replace("adm_list_", "").strip().upper()
    contas = list_stock_by_tipo(tipo, limit=10)

    if not contas:
        text = f"❌ Nenhuma conta encontrada para o tipo *{tipo}*."
        kb = kb_admin_list_tipos_para_remover()
    else:
        linhas = []
        for c in contas:
            status = "✅ DISP" if c["usado"] == 0 else "❌ USADA"
            linhas.append(f"ID: *{c['id']}* — `{c['email']}` — {status}")

        text = "📋 *Últimas contas do tipo* " + f"*{tipo}*:\n\n" + "\n".join(linhas)
        # teclado com botões de deletar por ID
        buttons = [
            [types.InlineKeyboardButton(
                text=f"❌ Remover ID {c['id']}",
                callback_data=f"adm_del_{c['id']}"
            )] for c in contas if c["usado"] == 0
        ]
        buttons.append([types.InlineKeyboardButton(text="⬅ Voltar tipos", callback_data="adm_estoque_list_tipos")])
        kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ===========================
# Remover uma conta específica do estoque
# ===========================
@router.callback_query(F.data.startswith("adm_del_"))
async def admin_delete_stock(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Você não é admin.", show_alert=True)

    sid = int(callback.data.replace("adm_del_", ""))
    delete_stock(sid)

    await callback.answer("Conta removida do estoque. ✅", show_alert=True)
    # Volta para seleção de tipos
    await admin_estoque_list_tipos(callback)


# ===========================
# Botão → Adicionar estoque (escolher tipo)
# ===========================
@router.callback_query(F.data == "adm_addstock")
async def admin_addstock(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Você não é admin.", show_alert=True)

    caption = "📦 *Adicionar estoque*\n\nSelecione o tipo da conta:"
    await callback.message.edit_text(
        caption,
        reply_markup=kb_admin_addstock_select()
    )
    await callback.answer()


# ===========================
# Menu de bônus de recarga
# ===========================
@router.callback_query(F.data == "adm_bonus")
async def admin_bonus_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Você não é admin.", show_alert=True)

    await callback.message.edit_text(
        "🎁 *CONFIGURAÇÃO DE BÔNUS DE RECARGA*\n\nEscolha um valor:",
        reply_markup=kb_admin_bonus()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_bonus_"))
async def admin_set_bonus(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Você não é admin.", show_alert=True)

    from models.users import set_bonus_percent

    percent = int(callback.data.replace("adm_bonus_", ""))
    set_bonus_percent(percent)

    await callback.message.edit_text(
        f"🎉 Bônus de recarga atualizado para *{percent}%*!",
        reply_markup=kb_admin_panel()
    )
    await callback.answer()


def register_admin_panel(dp):
    dp.include_router(router)
