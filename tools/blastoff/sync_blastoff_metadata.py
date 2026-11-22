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
    if '"blastoff_gs"' not in text.split("ROSTER = {")[1].split("}")[0]:
        target = '"swindle_gs":                   ("decepticon", "tech", 5),'
        replacement = target + '\n    "blastoff_gs":                  ("decepticon", "demo", 5),'
        text = text.replace(target, replacement, 1)

    # 2. _BOT_BASE_STATS
    if '"blastoff_gs"' not in text.split("_BOT_BASE_STATS = {")[1].split("}")[0]:
        target = '"swindle_gs": (38520, 2854),'
        replacement = target + '\n    "blastoff_gs": (46500, 3150),'
        text = text.replace(target, replacement, 1)

    # 3. _ART_BASE
    if '"blastoff_gs"' not in text.split("_ART_BASE = {")[1].split("}")[0]:
        target = '"swindle": "swindle_gs",'
        replacement = target + '\n    "blastoff_gs": "blastoff_gs",\n    "blastoff": "blastoff_gs",'
        text = text.replace(target, replacement, 1)

    # 4. _BOT_NAMES
    if '"blastoff_gs"' not in text.split("_BOT_NAMES = {")[1].split("}")[0]:
        target = '"swindle": "Swindle",'
        replacement = target + '\n    "blastoff_gs": "Blast Off",\n    "blastoff": "Blast Off",'
        text = text.replace(target, replacement, 1)

    # 5. OWNED Demo list (around line 1860)
    if '"blastoff_gs"' not in text:
        target = '"megatronus_gs_kabam",'
        replacement = target + '\n        "blastoff_gs",'
        text = text.replace(target, replacement, 1)

    gamedata_path.write_text(text, encoding="utf-8")
    print("[✓] Updated Server/gamedata.py with blastoff_gs (Demo class)")


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
            "blastoff_gs",
            "爆炸",
            "Blast Off",
            "decepticon",
            "demo",
            5,
            "Fall of Cybertron",
            1.0,
            1.0,
            0.5,
            1.0,
            "Fall of Cybertron",
            "霸天虎战车队（Combaticons）傲慢冷酷的空天打击与轨道轰炸兵。爆炸凭借卓越的空天航行能力与高能离子爆轰武器，能够从高空甚至轨道对敌军实施毁灭性的精准覆盖打击，变形为塞伯坦航天战机。",
            "An aloof and deadly Combaticon aerial sniper and orbital bombardier armed with ionic particle cannons who transforms into a Cybertronian space shuttle.",
            "战车队空天兵·爆破系",
            46500,
            3150,
            7850,
            "离子聚能爆轰",
            "Ionic Particle Cannon",
            "轨道折跃重袭",
            "Orbital Warp Dive",
            "塞伯坦空天灭绝",
            "Cybertronian Orbital Annihilation",
        ),
    )

    cur.execute("DELETE FROM character_abilities WHERE bot_id = ?", ("blastoff_gs",))
    abilities = [
        ("basic", "基础特长", "Basic Abilities", "离子爆轰、重装空防突击与高空火力压制。", "Ionic Bombardment, Heavy Aerial Assault & High-Altitude Suppression.", 0),
        ("sp1", "超强必杀 1 - 离子聚能爆轰", "SP1 - Ionic Particle Cannon", "手臂高能离子重炮聚集塞伯坦暗能量，射出超高压缩离子束贯穿目标防御并引发剧烈等离子爆轰。", "Gathers Cybertronian dark energy into the arm ionic cannon, firing an ultra-compressed particle beam that penetrates defenses.", 1),
        ("sp2", "超强必杀 2 - 轨道折跃重袭", "SP2 - Orbital Warp Dive", "启动背部超音速推进翼折跃突防，俯冲轰炸后展开重装近战痛击敌人！", "Engages supersonic booster wings to warp and dive-bomb, following up with heavy melee strikes.", 2),
        ("sp3", "超强必杀 3 - 塞伯坦空天灭绝", "SP3 - Cybertronian Orbital Annihilation", "升空变形为航天战机巡航掠袭，从轨道倾泻毁灭性聚能离子狂潮，以毁天灭地的战车队怒火彻底湮灭目标！", "Transforms into space shuttle mode to strafe and unleash a torrent of orbital ion artillery from high atmosphere.", 3),
    ]
    for cat, tz, te, dz, de, order in abilities:
        cur.execute(
            "INSERT INTO character_abilities (bot_id, category, title_zh, title_en, desc_zh, desc_en, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("blastoff_gs", cat, tz, te, dz, de, order),
        )
    conn.commit()
    conn.close()
    print("[✓] Updated Server/tftf_database.db with blastoff_gs")


def update_bot_names_zh():
    entry = {
        "en": "Blast Off",
        "zh": "爆炸",
        "faction": "霸天虎",
        "note": "战车队·爆破系",
        "desc": "战车队傲慢冷酷的空天打击与轨道轰炸兵。爆炸凭借卓越的空天航行能力与高能离子爆轰武器，能够从高空甚至轨道对敌军实施毁灭性的精准覆盖打击。"
    }
    for p in (ROOT / "bot_names_zh.json", SERVER_DIR / "bot_names_zh.json"):
        if not p.is_file():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        data["blastoff_gs"] = entry
        data["blastoff"] = entry
        p.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
        print(f"[✓] Updated {p.relative_to(ROOT)} with blastoff_gs & blastoff")


def update_sp3_timings():
    p = SERVER_DIR / "sp3_timings.json"
    if p.is_file():
        data = json.loads(p.read_text(encoding="utf-8"))
        data["blastoff_gs"] = {
            "intervals": [[2500, 5000]],
            "props": {},
            "notes": "爆炸 (Blast Off) - 塞伯坦航天战机 (基于震天尊骨架)",
        }
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("[✓] Updated Server/sp3_timings.json with blastoff_gs")


def update_special_attacks():
    p = ROOT / "assets" / "xlate" / "custom_special_attacks.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    bots = data.setdefault("bots", {})
    entry = {
        "display_name": "爆炸",
        "specials": [
            {
                "name": "离子聚能爆轰",
                "desc": "手臂高能离子重炮聚集塞伯坦暗能量，射出超高压缩离子束贯穿目标防御并引发剧烈等离子爆轰。",
            },
            {
                "name": "轨道折跃重袭",
                "desc": "启动背部超音速推进翼折跃突防，俯冲轰炸后展开重装近战痛击敌人！",
            },
            {
                "name": "塞伯坦空天灭绝",
                "desc": "升空变形为航天战机巡航掠袭，从轨道倾泻毁灭性聚能离子狂潮，以毁天灭地的战车队怒火彻底湮灭目标！",
            },
        ],
    }
    bots["blastoff"] = entry
    bots["blastoff_gs"] = entry
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("[✓] Updated assets/xlate/custom_special_attacks.json with blastoff & blastoff_gs")


def update_sp_callouts():
    p = SERVER_DIR / "abilities" / "sp_callouts.py"
    text = p.read_text(encoding="utf-8")
    if '"blastoff_gs"' not in text:
        target = '"swindle_gs": ("ID_SPECIAL_ATTACK_SWINDLE_GS_0", "ID_SPECIAL_ATTACK_SWINDLE_GS_1", "ID_SPECIAL_ATTACK_SWINDLE_GS_2"),'
        replacement = target + '\n    "blastoff_gs": ("ID_SPECIAL_ATTACK_BLASTOFF_GS_0", "ID_SPECIAL_ATTACK_BLASTOFF_GS_1", "ID_SPECIAL_ATTACK_BLASTOFF_GS_2"),\n    "blastoff": ("ID_SPECIAL_ATTACK_BLASTOFF_GS_0", "ID_SPECIAL_ATTACK_BLASTOFF_GS_1", "ID_SPECIAL_ATTACK_BLASTOFF_GS_2"),'
        text = text.replace(target, replacement, 1)
        p.write_text(text, encoding="utf-8")
        print("[✓] Updated Server/abilities/sp_callouts.py with blastoff_gs")


def update_hook_c():
    p = ROOT / "tools" / "nativehook" / "hook.c"
    text = p.read_text(encoding="utf-8")
    
    # 1. ART_BASE_MAP
    if '{ "blastoff_gs", "blastoff_gs" }' not in text:
        target = '{ "swindle_gs", "swindle_gs" },\n    { "swindle", "swindle_gs" },'
        replacement = target + '\n    { "blastoff_gs", "blastoff_gs" },\n    { "blastoff", "blastoff_gs" },'
        text = text.replace(target, replacement, 1)
        print("[✓] Added blastoff_gs & blastoff to ART_BASE_MAP in hook.c")

    # 2. Chinese name mapping in combat overlay
    if 'strstr(bot_id, "blastoff")' not in text:
        target = 'else if (strstr(bot_id, "swindle") != NULL) hero = "诈骗";'
        replacement = target + '\n            else if (strstr(bot_id, "blastoff") != NULL) hero = "爆炸";'
        text = text.replace(target, replacement, 1)
        print("[✓] Added blastoff Chinese name mapping to hook.c")

    # 3. Hook 162 localization bio
    if 'strstr(k, "BLASTOFF")' not in text:
        target = '        if (strstr(k, "BRAWL") || strstr(k, "brawl") || strstr(k, "Brawl")) {'
        replacement = """        if (strstr(k, "BLASTOFF") || strstr(k, "blastoff") || strstr(k, "Blastoff") || strstr(k, "BlastOff")) {
            if (strstr(k, "BIO") || strstr(k, "desc") || strstr(k, "DESC") || strstr(k, "Bio")) {
                return g_strnew ? g_strnew("战车队傲慢冷酷的空天打击与轨道轰炸兵。爆炸凭借卓越的空天航行能力与高能离子爆轰武器，能够从高空甚至轨道对敌军实施毁灭性的精准覆盖打击。") : r;
            }
            return g_strnew ? g_strnew("爆炸") : r;
        }
""" + target
        text = text.replace(target, replacement, 1)
        print("[✓] Added blastoff BIO & Name localization to hook_162 in hook.c")

    p.write_text(text, encoding="utf-8")


def update_inapk_server():
    p = ROOT / "tools" / "nativehook" / "inapk_server.c"
    if p.is_file():
        text = p.read_text(encoding="utf-8")
        if '"blastoff_gs"' not in text and '"swindle_gs"' in text:
            target = '"swindle_gs",'
            replacement = target + ' "blastoff_gs",'
            text = text.replace(target, replacement, 1)
            p.write_text(text, encoding="utf-8")
            print("[✓] Added blastoff_gs to inapk_server.c enemy pool")


def regenerate_outputs():
    # 1. Regenerate gamedata payloads and bot_info.h
    print("[*] Rebuilding Server gamedata and exporting bot_info.h...")
    subprocess.run([sys.executable, str(SERVER_DIR / "gamedata.py")], check=True, cwd=str(SERVER_DIR))

    # 2. Regenerate special_attacks_zh.h
    print("[*] Regenerating special_attacks_zh.h...")
    subprocess.run([sys.executable, str(ROOT / "tools" / "generate_special_attacks.py")], check=True, cwd=str(ROOT))

    # 3. Verify bot_info.h contains blastoff_gs
    bot_info_text = (ROOT / "tools" / "nativehook" / "bot_info.h").read_text(encoding="utf-8")
    for line in bot_info_text.splitlines():
        if "blastoff_gs" in line:
            print("  [bot_info.h verification]", line.strip())


def main():
    print("=== Synchronizing Blast Off Metadata across Server and NativeHook ===")
    update_gamedata_py()
    update_database()
    update_bot_names_zh()
    update_sp3_timings()
    update_special_attacks()
    update_sp_callouts()
    update_hook_c()
    update_inapk_server()
    regenerate_outputs()
    print("\n[✓] Blast Off (blastoff_gs, Demolition Class) metadata, database, localization, and headers completely synchronized!")


if __name__ == "__main__":
    main()
