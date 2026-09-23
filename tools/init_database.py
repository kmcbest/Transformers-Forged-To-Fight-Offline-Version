import sqlite3
import json
import os
import sys
from pathlib import Path

# Add Server directory to sys.path
sys.path.append(os.path.abspath("Server"))
import gamedata

DB_PATH = Path("Server/tftf_database.db")
JSON_ALL_PATH = Path("assets_redeco/tftf_all_characters.json")
BOT_NAMES_ZH_PATH = Path("Server/bot_names_zh.json")
FONT_PATH = Path("tools/web_dashboard/Tecnica_Bold_116.ttf")

def init_database():
    print(f"[*] Initializing TFTF SQLite Database at: {DB_PATH}")
    db_already_exists = DB_PATH.exists()
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    if db_already_exists:
        print("    [i] Database already exists, preserving user changes & ensuring schema...")

    # 1. Create Tables
    c.execute("""
    CREATE TABLE IF NOT EXISTS class_defaults (
        class_id TEXT PRIMARY KEY,
        name_zh TEXT NOT NULL,
        name_en TEXT NOT NULL,
        color_hex TEXT NOT NULL,
        pua_icon TEXT DEFAULT '',
        base_hp_mult REAL NOT NULL,
        base_atk_mult REAL NOT NULL,
        crit_chance REAL NOT NULL,
        crit_damage REAL NOT NULL,
        ranged_crit_bonus REAL DEFAULT 0.0,
        trait_zh TEXT DEFAULT '',
        sort_order INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS factions (
        faction_id TEXT PRIMARY KEY,
        name_zh TEXT NOT NULL,
        name_en TEXT NOT NULL,
        color_hex TEXT NOT NULL,
        pua_icon TEXT DEFAULT ''
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS characters (
        bot_id TEXT PRIMARY KEY,
        name_zh TEXT NOT NULL,
        name_en TEXT NOT NULL,
        faction TEXT NOT NULL,
        class TEXT NOT NULL,
        star_default INTEGER DEFAULT 5,
        source TEXT DEFAULT 'Kabam', -- 'Kabam', 'Netflix', 'Revival'
        health_mult REAL DEFAULT 1.0,
        attack_mult REAL DEFAULT 1.0,
        crit_chance REAL,
        crit_damage REAL,
        crit_chance_ranged REAL,
        crit_chance_melee REAL,
        block_proficiency REAL DEFAULT 0.5,
        mana_gain_mult REAL DEFAULT 1.0,
        origin TEXT DEFAULT '',
        desc_zh TEXT DEFAULT '',
        desc_en TEXT DEFAULT '',
        note TEXT DEFAULT '',
        pua_faction_icon TEXT DEFAULT '',
        pua_class_icon TEXT DEFAULT '',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(faction) REFERENCES factions(faction_id),
        FOREIGN KEY(class) REFERENCES class_defaults(class_id)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS character_abilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bot_id TEXT NOT NULL,
        category TEXT NOT NULL, -- 'basic', 'passive', 'signature', 'sp1', 'sp2', 'sp3', 'synergy'
        title_zh TEXT DEFAULT '',
        title_en TEXT DEFAULT '',
        desc_zh TEXT DEFAULT '',
        desc_en TEXT DEFAULT '',
        pua_icon TEXT DEFAULT '',
        raw_data_json TEXT DEFAULT '',
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY(bot_id) REFERENCES characters(bot_id) ON DELETE CASCADE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS pua_icons_cache (
        codepoint_hex TEXT PRIMARY KEY,
        codepoint_dec INTEGER NOT NULL,
        glyph_name TEXT NOT NULL,
        category TEXT DEFAULT 'misc'
    )
    """)

    # 2. Populate Class Defaults in Exact TFTF Advantage Wheel Order & Colors:
    class_rows = [
        ("tact", "战术系", "Tactician",  "#0543EF", "", 1.00, 1.00, 0.14, 1.50, 0.00, "战术克制。克制斗士系，依靠反制增益、虚弱破甲与协同加成。", 1),
        ("braw", "斗士系", "Brawler",    "#7D34BC", "", 1.25, 0.90, 0.08, 1.35, 0.00, "霸体近战肉搏。克制战士系，高血量与格挡反伤，强生存与强破防。", 2),
        ("warr", "战士系", "Warrior",    "#E9312D", "", 0.95, 1.15, 0.24, 1.55, 0.00, "高持续暴击。克制侦查系，依靠暴击触发流血(Bleed)等直接撕裂伤。", 3),
        ("scou", "侦查系", "Scout",      "#1D9F06", "", 0.85, 1.20, 0.32, 1.70, 0.00, "最高基础暴击、最高爆伤。克制科技系，敏捷刺客型，依靠闪避与连招爆发。", 4),
        ("tech", "科技系", "Tech",       "#09BCDD", "", 1.05, 0.95, 0.18, 1.50, 0.00, "能量与控制。克制爆破系，依靠能量汲取、护盾与焚烧控制，暴击作为稳定补充。", 5),
        ("demo", "爆破系", "Demolitions", "#F5BD0D", "", 1.10, 1.05, 0.14, 1.60, 0.21, "远程暴击特化。克制战术系，近战平稳，远程重炮射击暴击率大幅跃升至 35%。", 6),
    ]
    c.executemany("INSERT OR IGNORE INTO class_defaults VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", class_rows)

    # 3. Populate Factions
    faction_rows = [
        ("autobot",    "汽车人", "Autobot",    "#EF4444", ""),
        ("decepticon", "霸天虎", "Decepticon", "#8B5CF6", ""),
        ("predacon",   "原始兽", "Predacon",   "#10B981", ""),
        ("maximal",    "巨无霸", "Maximal",    "#3B82F6", ""),
    ]
    c.executemany("INSERT OR IGNORE INTO factions VALUES (?,?,?,?,?)", faction_rows)

    # 4. Populate PUA Icons Cache from Font
    print("    [+] Extracting PUA glyphs from Tecnica_Bold_116.ttf...")
    try:
        from fontTools.ttLib import TTFont
        tt = TTFont(str(FONT_PATH))
        cmap = tt.getBestCmap()
        pua_items = []
        for cp, name in cmap.items():
            if 0xE000 <= cp <= 0xF8FF:
                cat = "misc"
                if "shield" in name or "block" in name:
                    cat = "buff_shield"
                elif any(k in name for k in ["bleed", "poison", "stun", "mana", "sparkle", "heart"]):
                    cat = "buff_effect"
                elif any(k in name for k in ["ui_", "sort", "filter", "check", "circle", "plus", "minus"]):
                    cat = "ui_control"
                elif name.endswith(".sc"):
                    cat = "small_caps"
                pua_items.append((f"0x{cp:04x}", cp, name, cat))
        c.executemany("INSERT INTO pua_icons_cache VALUES (?,?,?,?)", pua_items)
        print(f"        -> Cached {len(pua_items)} PUA glyphs into database")
    except Exception as e:
        print(f"    [!] Failed to extract PUA glyphs: {e}")

    # 5. Load External Data Sources
    with open(BOT_NAMES_ZH_PATH, "r", encoding="utf-8") as f:
        bot_names_zh = json.load(f)

    with open(JSON_ALL_PATH, "r", encoding="utf-8") as f:
        wiki_all = json.load(f).get("characters", {})

    # Official bots mapping: strictly original Kabam characters from the official game
    OFFICIAL_BOTS_WIKI_MAP = {
        "arcee_gs_deluxe2014": "Arcee",
        "barricade_cin_dotm": "Barricade",
        "blaster_gs_leader2016": "Blaster",
        "bludgeon_gs_rd20": "Bludgeon",
        "bonecrusher_cin_rotf": "Bonecrusher",
        "bumblebee_cin_dotm": "Bumblebee (DOTM)",
        "bumblebee_gs_kabam": "Bumblebee",
        "cheetor_bw_transmetal": "Cheetor",
        "chromia_gs_kabam": "Chromia",
        "cliffjumper_gs_kabam": "Cliffjumper",
        "cyclonus_gs_uw06": "Cyclonus",
        "deadend_gs_deluxe2015": "Dead End",
        "dinobot_bw_kabam": "Dinobot",
        "dirge_gs_deluxe2008": "Dirge",
        "drift_cin_aoe": "Drift",
        "fte_optimus_gs_t3": "Optimus Prime",
        "fte_stars_gs_t3": "Starscream",
        "galvatron_gs_voyager2016": "Galvatron",
        "grimlock_gs_mp08": "Grimlock",
        "grindor_cin_rotf": "Grindor",
        "hotrod_cin_tlk": "Hot Rod",
        "hound_cin_tlk": "Hound",
        "ironhide_cin_rotf": "Ironhide (ROTF)",
        "ironhide_gs_kabam": "Ironhide",
        "jazz_gs_twm05": "Jazz",
        "jetfire_gs_leader2014": "Jetfire",
        "kickback_gs_kabam": "Kickback",
        "megatron_cin_rotf": "Megatron (ROTF)",
        "megatron_gs_leader2015": "Megatron",
        "megatronus_gs_kabam": "Megatronus",
        "mirage_gs_deluxe2016": "Mirage",
        "mixmaster_cin_rotf": "Mixmaster",
        "motormaster_gs_voyager2015": "Motormaster",
        "necrotronus_gs_kabam": "Necrotronus",
        "nemesisprime_gs_voyager2015": "Nemesis Prime",
        "optimusprime_cin_tf": "Optimus Prime (MV1)",
        "optimusprimal_bw_mp32": "Optimus Primal",
        "prowl_gs_deluxe2016": "Prowl",
        "ramjet_gs_deluxe2008": "Ramjet",
        "ratchet_gs_kabam": "Ratchet",
        "rhinox_gs_voyager2014": "Rhinox",
        "rodimusprime_gs_mp09": "Rodimus Prime",
        "scorponok_bw_kabam": "Scorponok",
        "sharkticon_gs_kabam": "Sharkticon",
        "sharkticon_gs_brawler": "Sharkticon",
        "sharkticon_gs_demolition": "Sharkticon",
        "sharkticon_gs_scout": "Sharkticon",
        "sharkticon_gs_tactician": "Sharkticon",
        "sharkticon_gs_tech": "Sharkticon",
        "sharkticon_gs_warrior": "Sharkticon",
        "shockwave_gs": "Shockwave",
        "sideswipe_gs": "Sideswipe",
        "skywarp_gs_leader2015": "Skywarp",
        "slipstream_gs": "Slipstream",
        "soundblaster_gs_mp13b": "Soundblaster_Tactician",
        "soundwave_gs": "Soundwave",
        "sunstreaker_gs_deluxe2008": "Sunstreaker",
        "tantrum_gs_kabam": "Tantrum",
        "thundercracker_gs_leader2015": "Thundercracker",
        "ultramagnus_gs_leader": "Ultra Magnus",
        "waspinator_gs_deluxe": "Waspinator",
        "wheeljack_gs_mp20": "Wheeljack",
        "windblade_gs": "Windblade",
    }

    # 6. Populate Characters & Abilities
    print("    [+] Populating 78 Characters and their Abilities...")
    char_count = 0
    ability_count = 0
    official_count = 0
    original_count = 0

    for bid, (faction, klass, star) in gamedata.ROSTER.items():
        zh_meta = bot_names_zh.get(bid, {})
        name_zh = zh_meta.get("zh", gamedata.display_name(bid, "zh"))
        name_en = zh_meta.get("en", gamedata.display_name(bid, "en"))
        desc_zh = zh_meta.get("desc", "")
        note = zh_meta.get("note", "")

        # Base stat overrides
        overrides = gamedata._BASE_STATS_OVERRIDE.get(bid, {})
        health_mult = overrides.get("health_mult", 1.0)
        attack_mult = overrides.get("attack_mult", 1.0)
        crit_chance = overrides.get("crit_chance", None)
        crit_damage = overrides.get("crit_damage", None)
        crit_chance_ranged = None
        crit_chance_melee = None

        # Character special rules
        if "thundercracker" in bid.lower():
            crit_chance_melee = 0.0 # Thundercracker signature: 0 melee crit
            crit_chance_ranged = 0.25
            note += " [特性: 0近战暴击，远程暴击率加成]"
        elif bid == "starscream_ghost_gs":
            crit_chance = 0.35
            crit_damage = 1.75
            note += " [特性: 鬼魂侦查系，全时悬浮飞行与高额暴击]"

        # Origin
        origin = "Generation 1"
        if "cin" in bid or "rotf" in bid or "dotm" in bid or "tlk" in bid or "aoe" in bid:
            origin = "Cinematic (Movie)"
        elif "bw" in bid:
            origin = "Beast Wars"
        elif "sg" in bid:
            origin = "Shattered Glass"

        # Source (Kabam / Netflix / Revival)
        if bid in ("chromia_gs_kabam", "deadend_gs_deluxe2015"):
            source = "Netflix"
        elif bid in OFFICIAL_BOTS_WIKI_MAP:
            source = "Kabam"
        else:
            source = "Revival"

        c.execute("""
        INSERT INTO characters (
            bot_id, name_zh, name_en, faction, class, star_default, source,
            health_mult, attack_mult, crit_chance, crit_damage,
            crit_chance_ranged, crit_chance_melee, block_proficiency, mana_gain_mult,
            origin, desc_zh, desc_en, note
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            bid, name_zh, name_en, faction, klass, star, source,
            health_mult, attack_mult, crit_chance, crit_damage,
            crit_chance_ranged, crit_chance_melee, 0.5, 1.0,
            origin, desc_zh, "", note
        ))
        char_count += 1

        # Check if official character
        if bid in OFFICIAL_BOTS_WIKI_MAP and OFFICIAL_BOTS_WIKI_MAP[bid] in wiki_all:
            wname = OFFICIAL_BOTS_WIKI_MAP[bid]
            wdata = wiki_all[wname]
            ga = wdata.get("game_abilities", {})
            sort_idx = 0
            official_count += 1

            # 1. Basic Abilities
            for basic in ga.get("basic_abilities", []):
                title = basic.split("-")[0].replace("*", "").strip() if "-" in basic else "基础特长"
                desc = basic.split("-", 1)[1].strip() if "-" in basic else basic.strip()
                c.execute("""
                INSERT INTO character_abilities (bot_id, category, title_zh, title_en, desc_zh, desc_en, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (bid, "basic", title, title, desc, basic, sort_idx))
                sort_idx += 1
                ability_count += 1

            # 2. Passive Abilities
            for pas in ga.get("abilities", []):
                lines = pas.strip().split("\n")
                title = lines[0].replace("*", "").strip()
                desc = "\n".join(lines[1:]) if len(lines) > 1 else lines[0]
                c.execute("""
                INSERT INTO character_abilities (bot_id, category, title_zh, title_en, desc_zh, desc_en, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (bid, "passive", title, title, desc, pas, sort_idx))
                sort_idx += 1
                ability_count += 1

            # 3. Signature Ability
            sig = ga.get("signature_ability", [])
            if sig:
                sig_title = sig[0].strip() if len(sig) > 0 else "觉醒能力"
                sig_desc = "\n\n".join(sig[1:]) if len(sig) > 1 else (sig[0] if len(sig) > 0 else "")
                c.execute("""
                INSERT INTO character_abilities (bot_id, category, title_zh, title_en, desc_zh, desc_en, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (bid, "signature", sig_title, sig_title, sig_desc, "\n".join(sig), sort_idx))
                sort_idx += 1
                ability_count += 1

            # 4. Special Attacks (SP1, SP2, SP3)
            specials = ga.get("special_attacks", [])
            for sp_i, sp in enumerate(specials[:3]):
                cat = f"sp{sp_i+1}"
                sp_title = f"特殊技 {sp_i+1}"
                sp_desc = sp.strip()
                if "#" in sp:
                    parts = sp.split("-", 1)
                    if len(parts) > 1:
                        sp_title = parts[0].replace("#", "").strip()
                        sp_desc = parts[1].strip()
                c.execute("""
                INSERT INTO character_abilities (bot_id, category, title_zh, title_en, desc_zh, desc_en, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (bid, cat, sp_title, sp_title, sp_desc, sp, sort_idx))
                sort_idx += 1
                ability_count += 1

            # 5. Synergies
            for syn in ga.get("synergy_bonuses", []):
                syn_title = syn.split("-")[0].replace("*", "").strip() if "-" in syn else "协同加成"
                syn_desc = syn.split("-", 1)[1].strip() if "-" in syn else syn.strip()
                c.execute("""
                INSERT INTO character_abilities (bot_id, category, title_zh, title_en, desc_zh, desc_en, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (bid, "synergy", syn_title, syn_title, syn_desc, syn, sort_idx))
                sort_idx += 1
                ability_count += 1

        else:
            # Original / Redeco bot: keep completely clean/empty in DB, user can add abilities via UI (+)
            original_count += 1

    conn.commit()
    conn.close()
    print(f"[OK] Database initialized successfully! ({char_count} bots: {official_count} official, {original_count} original; {ability_count} abilities)")

if __name__ == "__main__":
    init_database()
