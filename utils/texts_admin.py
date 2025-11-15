from models.users import total_client_saldo
from models.orders import get_total_vendas, get_total_faturado
from models.recharge import get_total_recargas
from models.stock import get_stock_summary


def texto_admin_dashboard():
    vendas = get_total_vendas()
    faturado = get_total_faturado()
    recargas = get_total_recargas()
    saldo_total = total_client_saldo()
    estoque = get_stock_summary()

    return f"""
🛠 *PAINEL ADMINISTRATIVO – DOCA STORE*

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

Selecione uma opção abaixo:
    """
