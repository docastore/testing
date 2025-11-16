import sqlite3
from contextlib import closing
from typing import Optional, Dict, Any
from .db import get_db
from config import DB_PATH


def _row_to_user(row) -> Dict[str, Any]:
    user_id, tg_id, doc_code, saldo, pontos = row
    return {
        "id": user_id,
        "telegram_id": tg_id,
        "doc_code": doc_code,
        "saldo": float(saldo),
        "pontos": float(pontos),
    }


def get_or_create_user(telegram_id: int) -> Dict[str, Any]:
    with closing(sqlite3.connect(DB_PATH)) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            "SELECT id, telegram_id, doc_code, saldo, pontos FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )
        row = cur.fetchone()

        if row:
            return _row_to_user(row)

        # Cria novo usuário
        cur.execute(
            "INSERT INTO users (telegram_id, saldo, pontos) VALUES (?, 0, 0)",
            (telegram_id,),
        )
        user_id = cur.lastrowid
        doc_code = f"DOC-{user_id:05d}"

        cur.execute(
            "UPDATE users SET doc_code = ? WHERE id = ?",
            (doc_code, user_id),
        )
        conn.commit()

        return {
            "id": user_id,
            "telegram_id": telegram_id,
            "doc_code": doc_code,
            "saldo": 0.0,
            "pontos": 0.0,
        }


def get_user_by_doc(doc_code: str) -> Optional[Dict[str, Any]]:
    with closing(sqlite3.connect(DB_PATH)) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            "SELECT id, telegram_id, doc_code, saldo, pontos FROM users WHERE doc_code = ?",
            (doc_code,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return _row_to_user(row)


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with closing(sqlite3.connect(DB_PATH)) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            "SELECT id, telegram_id, doc_code, saldo, pontos FROM users WHERE id = ?",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return _row_to_user(row)


def add_saldo(user_id: int, value: float) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute(
            "UPDATE users SET saldo = saldo + ? WHERE id = ?",
            (value, user_id),
        )


def add_saldo_by_doc(doc_code: str, value: float) -> Optional[Dict[str, Any]]:
    """
    Adiciona saldo usando DOC-ID. Retorna o usuário atualizado ou None se não existir.
    """
    with closing(sqlite3.connect(DB_PATH)) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute("SELECT id FROM users WHERE doc_code = ?", (doc_code,))
        row = cur.fetchone()
        if not row:
            return None

        user_id = row[0]
        cur.execute(
            "UPDATE users SET saldo = saldo + ? WHERE id = ?",
            (value, user_id),
        )

        cur.execute(
            "SELECT id, telegram_id, doc_code, saldo, pontos FROM users WHERE id = ?",
            (user_id,),
        )
        row = cur.fetchone()
        return _row_to_user(row)


# ===== CONFIG BÔNUS DE RECARGA =====

def get_bonus_percent() -> float:
    with closing(sqlite3.connect(DB_PATH)) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            "SELECT value FROM config WHERE key = 'bonus_recharge_percent';"
        )
        row = cur.fetchone()
        if not row:
            return 0.0
        try:
            return float(row[0])
        except ValueError:
            return 0.0


def set_bonus_percent(value: float) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute(
            """
            INSERT INTO config (key, value)
            VALUES ('bonus_recharge_percent', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (str(value),),
        )


def create_recharge(user_id: int, amount: float) -> Dict[str, Any]:
    bonus_percent = get_bonus_percent()
    bonus_amount = amount * (bonus_percent / 100.0)
    final_credit = amount + bonus_amount

    with closing(sqlite3.connect(DB_PATH)) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute(
            """
            INSERT INTO recharges (user_id, amount, bonus_percent, bonus_amount, final_credit, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
            """,
            (user_id, amount, bonus_percent, bonus_amount, final_credit),
        )
        rec_id = cur.lastrowid

    return {
        "id": rec_id,
        "user_id": user_id,
        "amount": amount,
        "bonus_percent": bonus_percent,
        "bonus_amount": bonus_amount,
        "final_credit": final_credit,
        "status": "pending",
    }


def total_client_saldo() -> float:
    with closing(sqlite3.connect(DB_PATH)) as conn, closing(conn.cursor()) as cur:
        cur.execute("SELECT SUM(saldo) FROM users")
        row = cur.fetchone()
        return float(row[0]) if row and row[0] is not None else 0.0


# -------- FUNÇÕES PARA WEBHOOK MP --------

def get_user_by_doc_code(doc_code: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE doc_code = ?", (doc_code,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    cols = [d[0] for d in cur.description]
    return dict(zip(cols, row))


def add_balance_by_doc(doc_code: str, amount: float):
    """
    Atualiza o saldo usando doc_code (chamado pelo webhook).
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET saldo = saldo + ?
        WHERE doc_code = ?
    """, (amount, doc_code))

    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    return updated

def update_recharge_message_id(recarga_id, message_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE recargas SET message_id = ? WHERE id = ?",
            (message_id, recarga_id)
        )
        conn.commit()

def update_recharge_message_id(recarga_id: int, message_id: int) -> None:
    """
    Salva o message_id da mensagem do Telegram onde foi enviado o QRCode do PIX.
    Tabela correta: recharges.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE recharges SET message_id = ? WHERE id = ?",
                (message_id, recarga_id),
            )
            conn.commit()
        except sqlite3.OperationalError as e:
            # Se por algum motivo a coluna não existir, cria e tenta de novo
            if "no such column: message_id" in str(e):
                cur.execute("ALTER TABLE recharges ADD COLUMN message_id INTEGER")
                conn.commit()
                cur.execute(
                    "UPDATE recharges SET message_id = ? WHERE id = ?",
                    (message_id, recarga_id),
                )
                conn.commit()
            else:
                raise


def get_last_recharge_by_doc(doc_code: str):
    """
    Retorna a última recarga (dict) para um DOC (external_reference),
    incluindo o message_id salvo.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT r.*
            FROM recharges r
            JOIN users u ON u.id = r.user_id
            WHERE u.doc_code = ?
            ORDER BY r.id DESC
            LIMIT 1
            """,
            (doc_code,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return dict(row)
