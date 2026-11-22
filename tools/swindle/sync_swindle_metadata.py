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
    if '"swindle_gs"' not in text.split("ROSTER = {")[1].split("}")[0]:
        target = '"brawl_gs":                     ("decepticon", "braw", 5),'
        replacement = target + '\n    "swindle_gs":                   ("decepticon", "tech", 5),'
        text = text.replace(target, replacement, 1)

    # 2. _BOT_BASE_STATS
    if '"swindle_gs"' not in text.split("_BOT_BASE_STATS = {")[1].split("}")[0]:
        target = '"brawl_gs": (45427, 3427),'
        replacement = target + '\n    "swindle_gs": (38520, 2854),'
        text = text.replace(target, replacement, 1)

    # 3. _ART_BASE
    if '"swindle_gs"' not in text.split("_ART_BASE = {")[1].split("}")[0]:
        target = '"brawl": "brawl_gs",'
        replacement = target + '\n    "swindle_gs": "swindle_gs",\n    "swindle": "swindle_gs",'
        text = text.replace(target, replacement, 1)

    # 4. _BOT_NAMES
    if '"swindle_gs"' not in text.split("_BOT_NAMES = {")[1].split("}")[0]:
        target = '"brawl": "Brawl",'
        replacement = target + '\n    "swindle_gs": "Swindle",\n    "swindle": "Swindle",'
        text = text.replace(target, replacement, 1)

    # 5. OWNED Tech list (around line 1840)
    if '"swindle_gs"' not in text:
        target = '"wheeljack_gs_mp20",'
        replacement = target + '\n        "swindle_gs",'
        text = text.replace(target, replacement, 1)

    gamedata_path.write_text(text, encoding="utf-8")
    print("[✓] Updated Server/gamedata.py with swindle_gs (Tech class)")


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
            "swindle_gs",
            "诈骗",
            "Swindle",
            "decepticon",
            "tech",
            5,
            "Fall of Cybertron",
            1.05,
            0.95,
            0.55,
            1.0,
            "Fall of Cybertron",
            "霸天虎战车队（Combaticons）狡黠贪婪的军火掮客与科技战术专家。随身携带全套高科技重炮与改装军火库，擅长在战场上以电磁震击与能量抽取瘫痪敌人，变形为塞伯坦高机动防空格斗战车。",
            "A cunning Combaticon arms dealer and tactical warfare specialist equipped with modular blasters who transforms into a Cybertronian combat jeep.",
            "战车队军火商·科技系",
            38520,
            2854,
            6708,
            "陀螺平衡破坏炮",
            "Gyro-Disruptor",
            "散射高爆离子弹",
            "Scatter Cluster Bomb",
            "战车突袭·军火狂潮",
            "Black Market Blitzkrieg",
        ),
    )

    cur.execute("DELETE FROM character_abilities WHERE bot_id = ?", ("swindle_gs",))
    abilities = [
        ("signature", "黑市护盾", "Black Market Shield", "如果敌人的攻击将诈骗的生命值降低到75%，50%或25%以下，黑市护盾将激活，100%降低敌人攻击造成的所有伤害，持续8秒。", "E515", 0),
        ("sp1", "陀螺平衡破坏炮", "Gyro-Disruptor", "手臂高能重炮发射陀螺干扰震荡弹，60%概率施加震击，造成攻击力200%的伤害，持续6秒；30%概率造成能量流失；10%概率造成眩晕。", "0xe914", 1),
        ("sp2", "散射高爆离子弹", "Scatter Cluster Bomb", "向近距离目标倾泻改装散射高爆离子弹，施加震击、能量流失与眩晕效果并重置模块升级。", "0xe914", 2),
        ("sp3", "战车突袭·军火狂潮", "Black Market Blitzkrieg", "变形为塞伯坦吉普战车全速撞击敌人，随后主炮与背部副炮火力全开近距饱和轰炸，重创并完全瘫痪目标！", "0xe914", 3),
        ("basic", "军火改装", "Weapon Mod", "构建进攻、防御或能量系统改装模块，全面强化机体战斗性能。", "E306", 4),
        ("basic", "震击", "Shock", "持续造成电磁能量伤害。", "E914", 5),
        ("basic", "能量流失", "Power Leak", "随时间推移持续扣减对手一定比例的能量槽。", "E607", 6),
        ("basic", "纳米修复", "Repair", "随时间推移持续修复生命值，或按受损比例回血。", "E503", 7),
        ("basic", "眩晕", "Stun", "临时阻止目标采取任何行动。", "E605", 8),
        ("passive", "黑市暴利", "Windfall", "如果诈骗得到三个同样的改装模块，会触发立即回血，恢复最大生命值的10~20%", "E503", 9),
    ]
    for cat, tz, te, dz, de, icon, order in [
        (a[0], a[1], a[2], a[3], a[3], a[4], a[5]) for a in abilities
    ]:
        cur.execute(
            "INSERT INTO character_abilities (bot_id, category, title_zh, title_en, desc_zh, desc_en, pua_icon, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("swindle_gs", cat, tz, te, dz, de, icon, order),
        )
    conn.commit()
    conn.close()
    print("[✓] Updated Server/tftf_database.db with swindle_gs")


def update_bot_names_zh():
    entry = {
        "en": "Swindle",
        "zh": "诈骗",
        "faction": "霸天虎",
        "note": "战车队·科技系",
        "desc": "战车队狡诈贪婪的军火专家与科技战术兵。诈骗掌握尖端塞伯坦改装军火与电磁震荡科技，装备高能陀螺破坏重炮，变形为塞伯坦高机动格斗战车。"
    }
    for p in (ROOT / "bot_names_zh.json", SERVER_DIR / "bot_names_zh.json"):
        if not p.is_file():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        data["swindle_gs"] = entry
        data["swindle"] = entry
        p.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
        print(f"[✓] Updated {p.relative_to(ROOT)} with swindle_gs & swindle")


def update_sp3_timings():
    p = SERVER_DIR / "sp3_timings.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    data["swindle_gs"] = {
        "intervals": [[266, 2366]],
        "props": {},
        "notes": "诈骗 (Swindle) - 塞伯坦突击战车 (基于千斤顶骨架)",
    }
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("[✓] Updated Server/sp3_timings.json with swindle_gs")


def update_special_attacks():
    p = ROOT / "assets" / "xlate" / "custom_special_attacks.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    bots = data.setdefault("bots", {})
    entry = {
        "display_name": "诈骗",
        "specials": [
            {
                "name": "陀螺平衡破坏炮",
                "desc": "手臂高能重炮发射陀螺干扰震荡弹，打乱对手平衡并造成严重电磁震击伤害。",
            },
            {
                "name": "散射高爆离子弹",
                "desc": "倾泻改装军火库的散射高爆离子弹，密集覆盖敌方阵地造成连续破坏并重组系统模块。",
            },
            {
                "name": "战车突袭·军火狂潮",
                "desc": "变形为高机动塞伯坦吉普战车全速撞击敌人，主炮与全套副炮火力全开饱和轰炸！",
            },
        ],
    }
    bots["swindle"] = entry
    bots["swindle_gs"] = entry
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("[✓] Updated assets/xlate/custom_special_attacks.json with swindle & swindle_gs")


def update_sp_callouts():
    p = SERVER_DIR / "abilities" / "sp_callouts.py"
    text = p.read_text(encoding="utf-8")
    if '"swindle_gs"' not in text:
        target = '"sunstreaker_gs_deluxe2008": ("ID_SPECIAL_ATTACK_SIDES_GS_0", "ID_SPECIAL_ATTACK_SIDES_GS_1", "ID_SPECIAL_ATTACK_SIDES_GS_2"),'
        replacement = target + '\n    "swindle_gs": ("ID_SPECIAL_ATTACK_SWINDLE_GS_0", "ID_SPECIAL_ATTACK_SWINDLE_GS_1", "ID_SPECIAL_ATTACK_SWINDLE_GS_2"),\n    "swindle": ("ID_SPECIAL_ATTACK_SWINDLE_GS_0", "ID_SPECIAL_ATTACK_SWINDLE_GS_1", "ID_SPECIAL_ATTACK_SWINDLE_GS_2"),'
        text = text.replace(target, replacement, 1)
        p.write_text(text, encoding="utf-8")
        print("[✓] Updated Server/abilities/sp_callouts.py with swindle_gs")


def update_hook_c():
    p = ROOT / "tools" / "nativehook" / "hook.c"
    text = p.read_text(encoding="utf-8")
    
    # 1. ART_BASE_MAP
    if '{ "swindle_gs", "swindle_gs" }' not in text:
        target = '{ "brawl_gs", "brawl_gs" },\n    { "brawl", "brawl" },'
        replacement = target + '\n    { "swindle_gs", "swindle_gs" },\n    { "swindle", "swindle_gs" },'
        text = text.replace(target, replacement, 1)
        print("[✓] Added swindle_gs & swindle to ART_BASE_MAP in hook.c")

    # 2. Chinese name mapping in combat overlay
    if 'strstr(bot_id, "swindle")' not in text:
        target = 'else if (strstr(bot_id, "brawl") != NULL) hero = "吵闹";'
        replacement = target + '\n            else if (strstr(bot_id, "swindle") != NULL) hero = "诈骗";'
        text = text.replace(target, replacement, 1)
        print("[✓] Added swindle Chinese name mapping to hook.c")

    p.write_text(text, encoding="utf-8")


def update_inapk_server():
    p = ROOT / "tools" / "nativehook" / "inapk_server.c"
    text = p.read_text(encoding="utf-8")
    if '"swindle_gs"' not in text:
        target = '"sunstreaker_gs_deluxe2008",'
        replacement = target + ' "swindle_gs",'
        text = text.replace(target, replacement, 1)
        p.write_text(text, encoding="utf-8")
        print("[✓] Added swindle_gs to inapk_server.c enemy pool")


def regenerate_outputs():
    # 1. Regenerate gamedata payloads and bot_info.h
    print("[*] Rebuilding Server gamedata and exporting bot_info.h...")
    subprocess.run([sys.executable, str(SERVER_DIR / "gamedata.py")], check=True, cwd=str(SERVER_DIR))

    # 2. Regenerate special_attacks_zh.h
    print("[*] Regenerating special_attacks_zh.h...")
    subprocess.run([sys.executable, str(ROOT / "tools" / "generate_special_attacks.py")], check=True, cwd=str(ROOT))

    # 3. Verify bot_info.h contains swindle_gs
    bot_info_text = (ROOT / "tools" / "nativehook" / "bot_info.h").read_text(encoding="utf-8")
    for line in bot_info_text.splitlines():
        if "swindle_gs" in line:
            print("  [bot_info.h verification]", line.strip())

    # 4. Validate swindle abilities via Quality Gate
    print("[*] Running validate_bot_ability.py for swindle_gs...")
    subprocess.run([sys.executable, str(ROOT / "tools" / "validate_bot_ability.py"), "swindle_gs"], check=True, cwd=str(ROOT))


def main():
    print("=== Synchronizing Swindle Metadata across Server and NativeHook ===")
    update_gamedata_py()
    update_database()
    update_bot_names_zh()
    update_sp3_timings()
    update_special_attacks()
    update_sp_callouts()
    update_hook_c()
    update_inapk_server()
    regenerate_outputs()
    print("\n[✓] Swindle (swindle_gs, Tech Class) metadata, database, localization, and headers completely synchronized!")


if __name__ == "__main__":
    main()
