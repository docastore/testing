import sqlite3
from contextlib import closing
from typing import Dict, Any, List, Tuple, Optional

from config import DB_PATH


# ===========================
# CRIAR PEDIDO + DEBITAR SALDO
# ===========================
def create_order_and_debit(
    user_id: int,
    categoria: str,
    tipo_code: str,
    tipo_label: str,
    price: float,
) -> Dict[str, Any]:
    """
    Debita o saldo do usuário (se tiver saldo suficiente) e cria um pedido.
    NÃO grava ainda o stock_id, isso é feito por link_order_to_stock().
    """
    with closing(sqlite3.connect(DB_PATH)) as conn, conn, closing(conn.cursor()) as cur:
        # Debita saldo com segurança
        cur.execute(
            "UPDATE users SET saldo = saldo - ? WHERE id = ? AND saldo >= ?",
            (price, user_id, price),
        )
        if cur.rowcount == 0:
            raise ValueError("Saldo insuficiente")

        # Cria o pedido
        cur.execute(
            """
            INSERT INTO orders (user_id, categoria, tipo_code, tipo_label, price, status)
            VALUES (?, ?, ?, ?, ?, 'completed')
            """,
            (user_id, categoria, tipo_code, tipo_label, price),
        )
        order_id = cur.lastrowid

        # Busca saldo atualizado
        cur.execute("SELECT saldo FROM users WHERE id = ?", (user_id,))
        saldo_row = cur.fetchone()
        new_saldo = saldo_row[0] if saldo_row else 0.0

    return {
        "id": order_id,
        "user_id": user_id,
        "categoria": categoria,
        "tipo_code": tipo_code,
        "tipo_label": tipo_label,
        "price": float(price),
        "saldo_atual": float(new_saldo),
    }


# ===========================
# VÍNCULO PEDIDO -> ESTOQUE
# ===========================
def _ensure_order_stock_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS order_stock (
            order_id INTEGER PRIMARY KEY,
            stock_id INTEGER NOT NULL
        );
        """
    )


def link_order_to_stock(order_id: int, stock_id: int) -> None:
    """
    Cria (ou sobrescreve) o vínculo entre um pedido e a conta de estoque entregue.
    """
    with closing(sqlite3.connect(DB_PATH)) as conn, conn, closing(conn.cursor()) as cur:
        _ensure_order_stock_table(cur)
        cur.execute(
            """
            INSERT OR REPLACE INTO order_stock (order_id, stock_id)
            VALUES (?, ?)
            """,
            (order_id, stock_id),
        )


# ===========================
# MÉTRICAS GERAIS (PAINEL ADMIN)
# ===========================
def get_total_vendas() -> int:
    with closing(sqlite3.connect(DB_PATH)) as conn, closing(conn.cursor()) as cur:
        cur.execute("SELECT COUNT(*) FROM orders")
        row = cur.fetchone()
        return int(row[0]) if row and row[0] is not None else 0


def get_total_faturado() -> float:
    with closing(sqlite3.connect(DB_PATH)) as conn, closing(conn.cursor()) as cur:
        cur.execute("SELECT SUM(price) FROM orders")
        row = cur.fetchone()
        return float(row[0]) if row and row[0] is not None else 0.0


def get_last_orders(limit: int = 10) -> List[Tuple]:
    with closing(sqlite3.connect(DB_PATH)) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            """
            SELECT id, user_id, categoria, tipo_label, price, created_at
            FROM orders
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cur.fetchall()


# ===========================
# HISTÓRICO DO USUÁRIO (PAGINADO)
# ===========================
def count_user_orders(user_id: int) -> int:
    with closing(sqlite3.connect(DB_PATH)) as conn, closing(conn.cursor()) as cur:
        cur.execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return int(row[0]) if row and row[0] is not None else 0


def get_user_orders_page(user_id: int, page: int, page_size: int = 5) -> List[Dict[str, Any]]:
    """
    Retorna uma página de pedidos de um usuário (5 por página por padrão),
    ordenados do mais recente para o mais antigo.
    """
    if page < 1:
        page = 1
    offset = (page - 1) * page_size

    with closing(sqlite3.connect(DB_PATH)) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            """
            SELECT id, tipo_label, price, created_at
            FROM orders
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, page_size, offset),
        )
        rows = cur.fetchall()

    result: List[Dict[str, Any]] = []
    for rid, tipo_label, price, created_at in rows:
        result.append(
            {
                "id": rid,
                "tipo_label": tipo_label,
                "price": float(price),
                "created_at": created_at,
            }
        )
    return result


# ===========================
# DETALHES DE UM PEDIDO + STOCK
# ===========================
def get_order_details(order_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Retorna detalhes do pedido, garantindo que pertence ao usuário,
    e tenta buscar o stock_id pela tabela order_stock.
    """
    with closing(sqlite3.connect(DB_PATH)) as conn, closing(conn.cursor()) as cur:
        _ensure_order_stock_table(cur)

        cur.execute(
            """
            SELECT o.id, o.user_id, o.tipo_label, o.price, o.created_at, s.stock_id
            FROM orders o
            LEFT JOIN order_stock s ON s.order_id = o.id
            WHERE o.id = ? AND o.user_id = ?
            """,
            (order_id, user_id),
        )
        row = cur.fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "user_id": row[1],
        "tipo_label": row[2],
        "price": float(row[3]),
        "created_at": row[4],
        "stock_id": row[5],  # pode ser None para pedidos antigos
    }
