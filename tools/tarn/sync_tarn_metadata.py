#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_tarn_metadata.py
Synchronizes Tarn (tarn_gs) across SQLite DB, localization JSONs, SP3 timings,
special attack strings, bot_info.h, and offline response payloads inside TFTF-blender.
Assigned class: Decepticon Brawler ("braw"), stats copied from Sunstreaker (飞毛腿, sunstreaker_gs_deluxe2008).
"""
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(r"E:\Agent\TFTF-blender")
SERVER_DIR = ROOT / "Server"
DB_PATH = SERVER_DIR / "tftf_database.db"


def update_database():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute(
        "SELECT hp, attack, rating, block_proficiency, mana_gain_mult FROM characters WHERE bot_id = 'sunstreaker_gs_deluxe2008'"
    )
    st_row = cur.fetchone()
    st_hp, st_atk, st_rating, st_bp, st_mg = st_row if st_row else (45022, 3637, 8146, 0.5, 1.0)
    print(f"[*] Fetched Sunstreaker baseline stats: HP={st_hp}, ATK={st_atk}, Rating={st_rating}")

    cur.execute(
        """
        INSERT INTO characters (
            bot_id, name_zh, name_en, faction, class, star_default, source,
            health_mult, attack_mult, crit_chance, crit_damage,
            crit_chance_ranged, crit_chance_melee, block_proficiency, mana_gain_mult,
            origin, desc_zh, desc_en, note, pua_faction_icon, pua_class_icon,
            hp, attack, rating,
            sp1_name_zh, sp1_name_en, sp2_name_zh, sp2_name_en, sp3_name_zh, sp3_name_en
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, NULL, NULL,
            NULL, NULL, ?, ?,
            ?, ?, ?, ?, '', '',
            ?, ?, ?,
            ?, ?, ?, ?, ?, ?
        )
        ON CONFLICT(bot_id) DO UPDATE SET
            name_zh=excluded.name_zh,
            name_en=excluded.name_en,
            faction=excluded.faction,
            class=excluded.class,
            star_default=excluded.star_default,
            source=excluded.source,
            health_mult=excluded.health_mult,
            attack_mult=excluded.attack_mult,
            crit_chance=NULL,
            crit_damage=NULL,
            block_proficiency=excluded.block_proficiency,
            mana_gain_mult=excluded.mana_gain_mult,
            origin=excluded.origin,
            desc_zh=excluded.desc_zh,
            desc_en=excluded.desc_en,
            note=excluded.note,
            hp=excluded.hp,
            attack=excluded.attack,
            rating=excluded.rating,
            sp1_name_zh=excluded.sp1_name_zh,
            sp1_name_en=excluded.sp1_name_en,
            sp2_name_zh=excluded.sp2_name_zh,
            sp2_name_en=excluded.sp2_name_en,
            sp3_name_zh=excluded.sp3_name_zh,
            sp3_name_en=excluded.sp3_name_en
        """,
        (
            "tarn_gs",
            "塔恩",
            "Tarn",
            "decepticon",
            "braw",
            5,
            "Revival",
            1.0,
            1.0,
            st_bp or 0.5,
            st_mg or 1.0,
            "IDW DJD",
            "霸天虎黑狗队 (D.J.D.) 领袖，狂热的霸天虎教条处刑者。右臂搭载双联融合炮，精通近战格斗摧毁与声波瓦解，变形为塞伯坦重型战地双管坦克。",
            "Leader of the Decepticon Justice Division. A relentless Brawler armed with a Double Fusion Cannon who transforms into a Cybertronian heavy tank.",
            "黑狗队领袖·斗士系 (飞毛腿数值)",
            st_hp,
            st_atk,
            st_rating,
            "双联融合点射",
            "Twin Fusion Burst",
            "黑狗重拳处刑",
            "D.J.D. Execution",
            "死亡之音：双管坦克轰击",
            "Voice of Execution",
        ),
    )

    cur.execute("DELETE FROM character_abilities WHERE bot_id = ?", ("tarn_gs",))
    abilities = [
        ("basic", "基础特长", "Basic Abilities", "近战打击、破甲冲击与融合炮能量压制。", "Melee Attacks, Armor Break & Fusion Cannon Suppression.", 0),
        ("sp1", "超强必杀 1 - 双联融合点射", "SP1 - Twin Fusion Burst", "以右臂双联融合炮连续轰击目标，造成高额能量伤害并破坏敌方护甲。", "Unleashes twin fusion blasts that deal heavy damage and break enemy armor.", 1),
        ("sp2", "超强必杀 2 - 黑狗重拳处刑", "SP2 - D.J.D. Execution", "重型格斗连击配合近距离融合炮齐射，彻底碾碎目标防御姿态。", "Heavy melee combo finished with point-blank double fusion cannon fire.", 2),
        ("sp3", "超强必杀 3 - 死亡之音：双管坦克轰击", "SP3 - Voice of Execution", "变形为塞伯坦双管坦克全速冲撞，随后展开双联主炮全力齐射，终结敌人。", "Transforms into a Cybertronian double-barreled tank to crush the foe with full-power firepower.", 3),
    ]
    for cat, tz, te, dz, de, order in abilities:
        cur.execute(
            "INSERT INTO character_abilities (bot_id, category, title_zh, title_en, desc_zh, desc_en, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("tarn_gs", cat, tz, te, dz, de, order),
        )
    conn.commit()
    conn.close()
    print("[✓] Updated Server/tftf_database.db (tarn_gs -> decepticon / braw / 5-star, 飞毛腿 stat mults 1.0/1.0)")


def update_bot_names_zh():
    entry = {
        "en": "Tarn",
        "zh": "塔恩",
        "faction": "霸天虎",
        "note": "黑狗队领袖·斗士系",
    }
    for p in (ROOT / "bot_names_zh.json", SERVER_DIR / "bot_names_zh.json"):
        if not p.is_file():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        data["tarn_gs"] = entry
        p.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
        print(f"[✓] Updated {p.relative_to(ROOT)} with tarn_gs")


def update_sp3_timings():
    p = SERVER_DIR / "sp3_timings.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    data["tarn_gs"] = {
        "intervals": [[3000, 5800]],
        "props": {},
        "notes": "塔恩 (Tarn) - 塞伯坦重型战地双管坦克 (基于通天晓骨架)",
    }
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("[✓] Updated Server/sp3_timings.json with tarn_gs")


def update_special_attacks():
    p = ROOT / "assets" / "xlate" / "custom_special_attacks.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    bots = data.setdefault("bots", {})
    sample = next(iter(bots.values()))
    print(f"[*] custom_special_attacks.json entry schema keys: {list(sample.keys())}")
    tarn_entry = {
        "display_name": "塔恩",
        "specials": [
            {
                "name": "双联融合点射",
                "desc": "右臂双联融合炮连续轰击目标，造成高额能量冲击并附加破甲减益。",
            },
            {
                "name": "黑狗重拳处刑",
                "desc": "切换近战重拳连段并近距离倾泻融合炮齐射，摧毁敌方护甲并造成沉重暴击打击。",
            },
            {
                "name": "死亡之音：坦克全功率齐射",
                "desc": "变形为塞伯坦双管重型坦克全速碾压突进，展开双联主炮释放毁灭级全功率齐射！",
            },
        ],
    }
    assert set(tarn_entry.keys()) == set(sample.keys()), f"Schema mismatch: {sample.keys()}"
    bots["tarn"] = tarn_entry
    bots["tarn_gs"] = tarn_entry
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("[✓] Updated assets/xlate/custom_special_attacks.json with tarn & tarn_gs")


def regenerate_outputs():
    sys.path.insert(0, str(SERVER_DIR))
    import gamedata

    # Check Sunstreaker vs Tarn computed stats
    st_hp, st_atk = gamedata.base_stats("sunstreaker_gs_deluxe2008", 5, 50)
    tn_hp, tn_atk = gamedata.base_stats("tarn_gs", 5, 50)
    print(f"[*] Rank5 Lv50 Stats Compare -> sunstreaker_gs_deluxe2008=({st_hp},{st_atk}), tarn_gs=({tn_hp},{tn_atk})")
    assert (st_hp, st_atk) == (tn_hp, tn_atk), f"Stats mismatch! {(st_hp, st_atk)} != {(tn_hp, tn_atk)}"

    gamedata.build_responses()
    gamedata.export_bot_info_header()

    # Regenerate special_attacks_zh.h
    subprocess.run([sys.executable, str(ROOT / "tools" / "generate_special_attacks.py")], check=True, cwd=str(ROOT))

    # Verify bot_info.h exact line for tarn_gs vs sunstreaker_gs_deluxe2008
    bot_info_text = (ROOT / "tools" / "nativehook" / "bot_info.h").read_text(encoding="utf-8")
    for line in bot_info_text.splitlines():
        if "sunstreaker_gs_deluxe2008" in line or "tarn_gs" in line:
            print("  [bot_info.h]", line.strip())


def main():
    update_database()
    update_bot_names_zh()
    update_sp3_timings()
    update_special_attacks()
    regenerate_outputs()
    print("\n[✓] Tarn (tarn_gs) metadata, database, localization, and headers synchronized!")


if __name__ == "__main__":
    main()
