import sqlite3
from contextlib import closing
from config import DB_PATH


def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn, conn, closing(conn.cursor()) as cur:

        # TABELA DE USUÁRIOS
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                doc_code TEXT UNIQUE,
                saldo REAL NOT NULL DEFAULT 0,
                pontos REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # TABELA DE ESTOQUE
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                email TEXT NOT NULL,
                senha TEXT NOT NULL,
                tutorial TEXT NOT NULL,
                usado INTEGER NOT NULL DEFAULT 0
            );
        """)

        # TABELA DE IMAGENS DAS CONTAS
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stock_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                FOREIGN KEY (stock_id) REFERENCES stock(id)
            );
        """)

        # TABELA DE PEDIDOS (ORDERS)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                categoria TEXT NOT NULL,
                tipo_code TEXT NOT NULL,
                tipo_label TEXT NOT NULL,
                price REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'completed',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)

        # TABELA DE RECARGAS (para quando ativar PIX automático)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recharges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                bonus_percent REAL NOT NULL,
                bonus_amount REAL NOT NULL,
                final_credit REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)

        # CONFIG GLOBAL
        cur.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)

        # BONUS DE RECARGA PADRÃO = 0%
        cur.execute("""
            INSERT OR IGNORE INTO config (key, value)
            VALUES ('bonus_recharge_percent', '0');
        """)

        print("📦 Banco inicializado com sucesso.")

        # TABELA PARA CONTROLAR PAGAMENTOS DO MERCADO PAGO JÁ PROCESSADOS
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mp_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL,
                status_detail TEXT,
                amount REAL NOT NULL,
                external_reference TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)

