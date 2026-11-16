import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import sqlite3

conn = sqlite3.connect(r"E:\Agent\TFTF-blender\Server\tftf_database.db")
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in c.fetchall()]
print("Tables in db:", tables)

for t in tables:
    try:
        c.execute(f"SELECT * FROM {t} WHERE bot_id='brawl_gs' OR bid='brawl_gs' OR id='brawl_gs'")
        rows = c.fetchall()
        if rows:
            print(f"Table {t}: found {len(rows)} rows for brawl_gs")
    except:
        pass
