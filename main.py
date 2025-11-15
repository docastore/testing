import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers.start import register_start_handlers
from handlers.menus import register_menu_handlers
from handlers.saldo import register_saldo_handlers
from handlers.admin import register_admin_handlers
from handlers.compras import register_compras_handlers
from handlers.estoque import register_estoque_handlers
from handlers.admin_panel import register_admin_panel
from database import init_db


async def main():
    print("🔵 Iniciando DOCA STORE BOT...")

    # Inicializa banco
    init_db()

    # AGORA NO PADRÃO ATUAL DO AIROGRAM 3.4+
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )

    dp = Dispatcher(storage=MemoryStorage())

    # Registrar todas as rotas / handlers
    register_start_handlers(dp)
    register_menu_handlers(dp)
    register_saldo_handlers(dp)
    register_admin_handlers(dp)
    register_compras_handlers(dp)
    register_estoque_handlers(dp)
    register_admin_panel(dp)


    # Iniciar o bot
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
