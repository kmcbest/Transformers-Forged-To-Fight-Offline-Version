import sys
import os
import json
import sqlite3
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "Server" / "tftf_database.db"
OUTPUT_DIR = ROOT / "Server" / "character_data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

def clean_comment(text: str) -> str:
    if not text:
        return ""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        if "//" in line:
            line = line.split("//")[0]
        cleaned.append(line.rstrip())
    import re
    return re.sub(r'\n{3,}', '\n\n', "\n".join(cleaned)).strip()

cur.execute("SELECT bot_id, name_zh, name_en, faction, class, sp1_name_zh, sp1_name_en, sp2_name_zh, sp2_name_en, sp3_name_zh, sp3_name_en FROM characters")
all_chars = cur.fetchall()

for c in all_chars:
    bid, name_zh, name_en, faction, bot_class, sp1_zh, sp1_en, sp2_zh, sp2_en, sp3_zh, sp3_en = c

    # 1. Signature
    cur.execute("SELECT title_zh, title_en, desc_zh, pua_icon FROM character_abilities WHERE bot_id=? AND category='signature'", (bid,))
    sig_row = cur.fetchone()
    sig_data = {
        "title_zh": sig_row[0] if sig_row else "",
        "title_en": sig_row[1] if sig_row else "",
        "desc_zh": clean_comment(sig_row[2]) if sig_row else "",
        "pua_icon": sig_row[3].strip() if (sig_row and sig_row[3]) else "",
        "ui_trigger": "none"
    }

    # 2. Special attacks
    specials = {}
    for idx, (cat, name_z, name_e) in enumerate([("sp1", sp1_zh, sp1_en), ("sp2", sp2_zh, sp2_en), ("sp3", sp3_zh, sp3_en)], start=1):
        cur.execute("SELECT title_zh, title_en, desc_zh, pua_icon FROM character_abilities WHERE bot_id=? AND category=?", (bid, cat))
        sp_rows = cur.fetchall()
        effects = []
        for s_zh, s_en, sd_zh, sp_icon in sp_rows:
            effects.append({
                "title_zh": s_zh,
                "title_en": s_en or "",
                "desc_zh": clean_comment(sd_zh),
                "pua_icon": sp_icon.strip() if sp_icon else ""
            })
        first_row = sp_rows[0] if sp_rows else ("", "", "", "")
        specials[cat] = {
            "name_zh": name_z or first_row[0] or f"SP{idx}",
            "name_en": name_e or first_row[1] or f"SP{idx}",
            "desc_zh": clean_comment(first_row[2]),
            "pua_icon": first_row[3].strip() if first_row[3] else "",
            "ui_trigger": f"onSpecial{idx}Hit",
            "effects": effects
        }

    # 3. Basic Abilities (基础能力卡片，渲染在上方卡片区与弹窗顶部"能力会随着升阶而提升")
    cur.execute("SELECT title_zh, title_en, desc_zh, pua_icon FROM character_abilities WHERE bot_id=? AND category='basic' ORDER BY sort_order", (bid,))
    basic_rows = cur.fetchall()
    basic_list = []
    for t_zh, t_en, d_zh, p_icon in basic_rows:
        if not t_zh or "基础特长" in t_zh:
            continue
        basic_list.append({
            "title_zh": t_zh.strip(),
            "title_en": (t_en or "").strip(),
            "desc_zh": clean_comment(d_zh),
            "pua_icon": p_icon.strip() if p_icon else "",
            "category": "basic",
            "ui_trigger": "none",
            "show_on_main_screen": True
        })

    # 4. Game Abilities (实战被动特长，展开在下方分类，以专属技能名为分类标题，不调用“被动”官方字段)
    cur.execute("SELECT title_zh, title_en, desc_zh, pua_icon FROM character_abilities WHERE bot_id=? AND category='passive' ORDER BY sort_order", (bid,))
    passive_rows = cur.fetchall()
    game_list = []
    for t_zh, t_en, d_zh, p_icon in passive_rows:
        if not t_zh or "基础特长" in t_zh:
            continue
        name = t_zh.strip()
        game_list.append({
            "title_zh": name,
            "title_en": (t_en or "").strip(),
            "desc_zh": clean_comment(d_zh),
            "pua_icon": p_icon.strip() if p_icon else "",
            "category": "passive",
            "ui_trigger": name,
            "show_on_main_screen": False
        })

    # Combined abilities list for legacy compatibility
    abilities_list = list(basic_list) + list(game_list)

    # 5. Synergies
    cur.execute("SELECT title_zh, title_en, desc_zh, pua_icon, synergy_bots FROM character_abilities WHERE bot_id=? AND category='synergy' ORDER BY sort_order", (bid,))
    syn_rows = cur.fetchall()
    synergies_list = []
    for s_zh, s_en, sd_zh, sp_icon, sb_json in syn_rows:
        try:
            b_heroes = json.loads(sb_json) if sb_json else []
        except Exception:
            b_heroes = []
        synergies_list.append({
            "title_zh": s_zh,
            "title_en": s_en or "",
            "desc_zh": clean_comment(sd_zh),
            "pua_icon": sp_icon.strip() if sp_icon else "",
            "bonus_heroes": b_heroes
        })

    bot_payload = {
        "bot_id": bid,
        "name_zh": name_zh,
        "name_en": name_en,
        "faction": faction,
        "class": bot_class,
        "signature": sig_data,
        "special_attacks": specials,
        "basic_abilities": basic_list,
        "game_abilities": game_list,
        "abilities": abilities_list,
        "synergies": synergies_list
    }

    out_file = OUTPUT_DIR / f"{bid}.json"
    out_file.write_text(json.dumps(bot_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

conn.close()
print(f"Successfully refreshed {len(all_chars)} bot json files in {OUTPUT_DIR}")
