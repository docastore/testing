import sqlite3
from contextlib import closing

from config import DB_PATH


def get_total_recargas() -> int:
    """
    Conta quantas recargas existem na tabela 'recharges'
    (usado no dashboard admin).
    """
    with closing(sqlite3.connect(DB_PATH)) as conn, closing(conn.cursor()) as cur:
        cur.execute("SELECT COUNT(*) FROM recharges")
        row = cur.fetchone()
        return int(row[0]) if row and row[0] is not None else 0
