# models/mp_payments.py
import sqlite3
from contextlib import closing

from config import DB_PATH


def mark_payment_if_new(
    payment_id: str,
    status: str,
    status_detail: str,
    amount: float,
    external_reference: str,
) -> bool:
    """
    Tenta registrar o pagamento na tabela mp_payments.
    Retorna True se FOI inserido agora (primeira vez),
    False se já existia (já processado antes).
    """
    with closing(sqlite3.connect(DB_PATH)) as conn, closing(conn.cursor()) as cur:
        try:
            cur.execute(
                """
                INSERT INTO mp_payments
                    (payment_id, status, status_detail, amount, external_reference)
                VALUES (?, ?, ?, ?, ?)
                """,
                (payment_id, status, status_detail, amount, external_reference),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # payment_id já existe (UNIQUE), então já processamos esse pagamento antes
            return False
