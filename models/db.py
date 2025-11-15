# models/db.py
import sqlite3
from pathlib import Path

# Caminho do arquivo do banco (ajusta o nome se o seu for outro)
DB_PATH = Path(__file__).resolve().parent.parent / "docastore.db"

def get_db():
    """
    Abre uma conexão com o banco SQLite e retorna o connection.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # permite acessar colunas por nome
    return conn
