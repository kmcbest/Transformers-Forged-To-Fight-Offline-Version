from pathlib import Path

fpath = Path(r"E:\Agent\TFTF-blender\Server\gamedata.py")
text = fpath.read_text(encoding="utf-8")

# 1. _ART_BASE
old_art = '"demolishor_gs": "demolishor_gs",'
new_art = '"demolishor_gs": "demolishor_gs",\n    "onslaught_gs": "onslaught_gs",'

# 2. _BOT_NAMES
old_bot = '"demolishor_gs": "Demolishor",'
new_bot = '"demolishor_gs": "Demolishor",\n    "onslaught_gs": "Onslaught",'

if old_art in text and old_bot in text:
    text = text.replace(old_art, new_art, 1)
    text = text.replace(old_bot, new_bot, 1)
    fpath.write_text(text, encoding="utf-8")
    print("[OK] Updated Server/gamedata.py successfully!")
else:
    print("[!] Target strings not found.")
