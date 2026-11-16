import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import sqlite3

conn = sqlite3.connect(r"E:\Agent\TFTF-blender\Server\tftf_database.db")
c = conn.cursor()
for t in ['characters', 'character_abilities']:
    c.execute(f"PRAGMA table_info({t})")
    cols = [r[1] for r in c.fetchall()]
    print(f"Table {t} cols: {cols}")
    c.execute(f"SELECT * FROM {t} WHERE bot_id='tarn_gs' OR bot_id='brawl_gs'")
    rows = c.fetchall()
    print(f"  Rows for tarn_gs / brawl_gs: {len(rows)}")
