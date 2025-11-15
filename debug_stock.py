import sqlite3

DB = "docastore.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Corrige o problema AMZ10P → AMZ_10P
cur.execute("""
UPDATE stock 
SET tipo = 'AMZ_10P'
WHERE tipo = 'AMZ10P';
""")

conn.commit()
conn.close()

print("✔ Estoque corrigido: AMZ10P → AMZ_10P")
