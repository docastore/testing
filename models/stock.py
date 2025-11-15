import sqlite3
from contextlib import closing
from typing import List, Dict, Any, Optional

from config import DB_PATH


def create_stock(
    tipo: str,
    email: str,
    senha: str,
    tutorial: str,
) -> Dict[str, Any]:
    with closing(sqlite3.connect(DB_PATH)) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute(
            """
            INSERT INTO stock (tipo, email, senha, tutorial, usado)
            VALUES (?, ?, ?, ?, 0)
            """,
            (tipo, email, senha, tutorial),
        )
        stock_id = cur.lastrowid

    return {
        "id": stock_id,
        "tipo": tipo,
        "email": email,
        "senha": senha,
        "tutorial": tutorial,
        "usado": 0,
    }


def add_stock_image(stock_id: int, file_id: str) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute(
            """
            INSERT INTO stock_images (stock_id, file_id)
            VALUES (?, ?)
            """,
            (stock_id, file_id),
        )


def get_stock_images(stock_id: int) -> List[str]:
    with closing(sqlite3.connect(DB_PATH)) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            "SELECT file_id FROM stock_images WHERE stock_id = ?",
            (stock_id,),
        )
        rows = cur.fetchall()
    return [r[0] for r in rows]


def get_one_available_stock(tipo: str) -> Optional[Dict[str, Any]]:
    with closing(sqlite3.connect(DB_PATH)) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            """
            SELECT id, tipo, email, senha, tutorial, usado
            FROM stock
            WHERE tipo = ? AND usado = 0
            ORDER BY id ASC
            LIMIT 1
            """,
            (tipo,),
        )
        row = cur.fetchone()

        if not row:
            return None

        stock_id, tipo, email, senha, tutorial, usado = row

        cur.execute(
            "SELECT file_id FROM stock_images WHERE stock_id = ?",
            (stock_id,),
        )
        img_rows = cur.fetchall()

    imagens = [r[0] for r in img_rows]

    return {
        "id": stock_id,
        "tipo": tipo,
        "email": email,
        "senha": senha,
        "tutorial": tutorial,
        "usado": usado,
        "imagens": imagens,
    }


def mark_stock_used(stock_id: int) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute(
            "UPDATE stock SET usado = 1 WHERE id = ?",
            (stock_id,),
        )


def get_stock_summary() -> Dict[str, Dict[str, int]]:
    tipos = ["AMZ_DIG", "AMZ_MIX", "AMZ_PRIME", "AMZ_10P"]
    summary = {t: {"disp": 0} for t in tipos}

    with closing(sqlite3.connect(DB_PATH)) as conn, closing(conn.cursor()) as cur:
        for t in tipos:
            cur.execute(
                "SELECT COUNT(*) FROM stock WHERE tipo = ? AND usado = 0",
                (t,),
            )
            row = cur.fetchone()
            summary[t]["disp"] = int(row[0]) if row and row[0] is not None else 0

    return summary


def list_stock_by_tipo(tipo: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Lista até 'limit' contas de um tipo (usadas ou não),
    para o painel admin poder mostrar e excluir.
    """
    with closing(sqlite3.connect(DB_PATH)) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            """
            SELECT id, email, usado
            FROM stock
            WHERE tipo = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (tipo, limit),
        )
        rows = cur.fetchall()

    result = []
    for rid, email, usado in rows:
        result.append(
            {
                "id": rid,
                "email": email,
                "usado": int(usado),
            }
        )
    return result


def delete_stock(stock_id: int) -> None:
    """
    Remove uma conta do estoque (e suas imagens).
    """
    with closing(sqlite3.connect(DB_PATH)) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute("DELETE FROM stock_images WHERE stock_id = ?", (stock_id,))
        cur.execute("DELETE FROM stock WHERE id = ?", (stock_id,))


def get_full_stock_by_id(stock_id: int):
    with closing(sqlite3.connect(DB_PATH)) as conn, closing(conn.cursor()) as cur:
        cur.execute("""
            SELECT id, tipo, email, senha, tutorial, usado
            FROM stock
            WHERE id = ?
        """, (stock_id,))
        row = cur.fetchone()

        if not row:
            return None

        st_id, tipo, email, senha, tutorial, usado = row

        cur.execute("SELECT file_id FROM stock_images WHERE stock_id = ?", (st_id,))
        imgs = [i[0] for i in cur.fetchall()]

    return {
        "id": st_id,
        "tipo": tipo,
        "email": email,
        "senha": senha,
        "tutorial": tutorial,
        "usado": usado,
        "imagens": imgs
    }
