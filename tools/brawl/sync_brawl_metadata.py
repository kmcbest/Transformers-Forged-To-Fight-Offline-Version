import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import sqlite3
import subprocess
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
SERVER_DIR = ROOT / "Server"
DB_PATH = SERVER_DIR / "tftf_database.db"


def update_gamedata_py():
    gamedata_path = SERVER_DIR / "gamedata.py"
    text = gamedata_path.read_text(encoding="utf-8")
    
    # 1. ROSTER
    if '"brawl_gs"' not in text.split("ROSTER = {")[1].split("}")[0]:
        target = '"tarn_gs":                      ("decepticon", "braw", 5),'
        replacement = target + '\n    "brawl_gs":                     ("decepticon", "braw", 5),'
        text = text.replace(target, replacement, 1)

    # 2. _BOT_BASE_STATS
    if '"brawl_gs"' not in text.split("_BOT_BASE_STATS = {")[1].split("}")[0]:
        target = '"tantrum_gs_kabam": (44850, 3590),'
        replacement = target + '\n    "brawl_gs": (45427, 3427),'
        text = text.replace(target, replacement, 1)

    # 3. _ART_BASE
    if '"brawl_gs"' not in text.split("_ART_BASE = {")[1].split("}")[0]:
        target = '"tarn_gs": "tarn_gs",'
        replacement = target + '\n    "brawl_gs": "brawl_gs",\n    "brawl": "brawl_gs",'
        text = text.replace(target, replacement, 1)

    # 4. _BOT_NAMES
    if '"brawl_gs"' not in text.split("_BOT_NAMES = {")[1].split("}")[0]:
        target = '"tarn_gs": "Tarn",'
        replacement = target + '\n    "brawl_gs": "Brawl",\n    "brawl": "Brawl",'
        text = text.replace(target, replacement, 1)

    gamedata_path.write_text(text, encoding="utf-8")
    print("[✓] Updated Server/gamedata.py with brawl_gs")


def update_database():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

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
            "brawl_gs",
            "吵闹",
            "Brawl",
            "decepticon",
            "braw",
            5,
            "Revival",
            1.0,
            1.0,
            0.5,
            1.0,
            "Fall of Cybertron",
            "霸天虎战车队（Combaticons）暴躁狂怒的陆战强袭专家。性格粗暴好战，装备重型装甲、高能突击重炮与背部双联副炮，变形为塞伯坦重型重炮战车。",
            "A hot-tempered Combaticon heavy warfare specialist armed with an assault cannon and dual back turrets who transforms into a Cybertronian battle tank.",
            "战车队突击兵·斗士系",
            45427,
            3427,
            7938,
            "巨碾碎裂击",
            "Seismic Crusher",
            "塞伯坦聚能炮击",
            "Cybertronian Blast",
            "战地重坦终极碾压",
            "Heavy Tank Annihilation",
        ),
    )

    cur.execute("DELETE FROM character_abilities WHERE bot_id = ?", ("brawl_gs",))
    abilities = [
        ("basic", "基础特长", "Basic Abilities", "重拳压制、狂暴破甲冲击与重炮爆轰。", "Heavy Melee Pressure, Armor Break & Cannon Explosions.", 0),
        ("sp1", "超强必杀 1 - 巨碾碎裂击", "SP1 - Seismic Crusher", "以战车重装巨臂猛砸地面释放毁灭震波，随后前冲连击碾碎敌人！", "Slams the ground with armored crushing arms to trigger seismic shockwaves, followed by a charging tackle.", 1),
        ("sp2", "超强必杀 2 - 塞伯坦聚能炮击", "SP2 - Cybertronian Blast", "汇聚极核高能等离子，向近距离目标倾泻毁天灭地的连续重炮爆轰！", "Charges the core plasma blaster and unleashes devastating point-blank cannon artillery.", 2),
        ("sp3", "超强必杀 3 - 战地重坦终极碾压", "SP3 - Heavy Tank Annihilation", "变形为塞伯坦重型突击战车高速冲击撞翻目标，主炮抵近轰击并以全重力将对手碾入地底！", "Transforms into a heavy Cybertronian assault tank to slam, bombard, and crush the target beneath heavy treads.", 3),
    ]
    for cat, tz, te, dz, de, order in abilities:
        cur.execute(
            "INSERT INTO character_abilities (bot_id, category, title_zh, title_en, desc_zh, desc_en, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("brawl_gs", cat, tz, te, dz, de, order),
        )
    conn.commit()
    conn.close()
    print("[✓] Updated Server/tftf_database.db with brawl_gs")


def update_bot_names_zh():
    entry = {
        "en": "Brawl",
        "zh": "吵闹",
        "faction": "霸天虎",
        "note": "战车队·斗士系",
        "desc": "战车队暴躁凶悍的重装突击兵。吵闹热衷喧嚣与破坏，搭载高威能塞伯坦主炮与背部副炮群，能够在战场上撕裂敌阵并进行毁灭性火力压制。"
    }
    for p in (ROOT / "bot_names_zh.json", SERVER_DIR / "bot_names_zh.json"):
        if not p.is_file():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        data["brawl_gs"] = entry
        data["brawl"] = entry
        p.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
        print(f"[✓] Updated {p.relative_to(ROOT)} with brawl_gs & brawl")


def update_sp3_timings():
    p = SERVER_DIR / "sp3_timings.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    data["brawl_gs"] = {
        "intervals": [[2500, 5000]],
        "props": {},
        "notes": "吵闹 (Brawl) - 塞伯坦重型重炮战车 (基于威震天骨架)",
    }
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("[✓] Updated Server/sp3_timings.json with brawl_gs")


def update_special_attacks():
    p = ROOT / "assets" / "xlate" / "custom_special_attacks.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    bots = data.setdefault("bots", {})
    brawl_entry = {
        "display_name": "吵闹",
        "specials": [
            {
                "name": "巨碾碎裂击",
                "desc": "以战车重装巨臂猛砸地面释放毁灭震波，随后前冲连击碾碎敌人！",
            },
            {
                "name": "塞伯坦聚能炮击",
                "desc": "汇聚极核高能等离子，向近距离目标倾泻毁天灭地的连续重炮爆轰！",
            },
            {
                "name": "战地重坦终极碾压",
                "desc": "变形为塞伯坦重型突击战车高速冲击撞翻目标，主炮抵近轰击并以全重力将对手碾入地底！",
            },
        ],
    }
    bots["brawl"] = brawl_entry
    bots["brawl_gs"] = brawl_entry
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("[✓] Updated assets/xlate/custom_special_attacks.json with brawl & brawl_gs")


def update_hook_c():
    p = ROOT / "tools" / "nativehook" / "hook.c"
    text = p.read_text(encoding="utf-8")
    
    # 1. ART_BASE_MAP
    if '{ "brawl_gs", "brawl_gs" }' not in text:
        target = '{ "bonecrusher_cin_rotf", "bonec_c" },'
        replacement = target + '\n    { "brawl_gs", "brawl_gs" },\n    { "brawl", "brawl" },'
        text = text.replace(target, replacement, 1)
        print("[✓] Added brawl_gs & brawl to ART_BASE_MAP in hook.c")

    # 2. Chinese name mapping in combat overlay
    if 'strstr(bot_id, "brawl")' not in text:
        target = 'else if (strstr(bot_id, "bonecrusher") != NULL) hero = "碎骨魔";'
        replacement = target + '\n            else if (strstr(bot_id, "brawl") != NULL) hero = "吵闹";'
        text = text.replace(target, replacement, 1)
        print("[✓] Added brawl Chinese name mapping to hook.c")

    p.write_text(text, encoding="utf-8")


def regenerate_outputs():
    # 1. Regenerate gamedata payloads and bot_info.h
    print("[*] Rebuilding Server gamedata and exporting bot_info.h...")
    subprocess.run([sys.executable, str(SERVER_DIR / "gamedata.py")], check=True, cwd=str(SERVER_DIR))

    # 2. Regenerate special_attacks_zh.h
    print("[*] Regenerating special_attacks_zh.h...")
    subprocess.run([sys.executable, str(ROOT / "tools" / "generate_special_attacks.py")], check=True, cwd=str(ROOT))

    # 3. Verify bot_info.h contains brawl_gs
    bot_info_text = (ROOT / "tools" / "nativehook" / "bot_info.h").read_text(encoding="utf-8")
    for line in bot_info_text.splitlines():
        if "brawl_gs" in line:
            print("  [bot_info.h verification]", line.strip())


def main():
    print("=== Synchronizing Brawl Metadata across Server and NativeHook ===")
    update_gamedata_py()
    update_database()
    update_bot_names_zh()
    update_sp3_timings()
    update_special_attacks()
    update_hook_c()
    regenerate_outputs()
    print("\n[✓] Brawl (brawl_gs) metadata, database, localization, and headers completely synchronized!")


if __name__ == "__main__":
    main()
