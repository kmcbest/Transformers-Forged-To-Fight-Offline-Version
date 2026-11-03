#!/usr/bin/env python3
"""
Sync updated basic abilities from Upstash KV to local repository:
1. Update D:\#E\Personal\kmcbest.github.io\tftfr\data\characters\{bot_id}.json
2. Update Server/character_data/{bot_id}.json
3. Update Server/tftf_database.db (character_abilities table where category = 'basic')
4. Rebuild tools/basic_abilities.json and sync to website data dir
5. Regenerate Server/gamedata.py and build/tftf_offline_payload.bin
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
import re
import json
import sqlite3
import shutil
import urllib.request
from pathlib import Path
from collections import defaultdict
from datetime import datetime

UPSTASH_URL = "https://deciding-bulldog-136761.upstash.io"
WRITE_TOKEN = "gQAAAAAAAhY5AAIgcDEyZGMwZDRhNzRlZGQ0MDI2YWM2YmI3ZDExNTc3ZjZmNA"

HERE = Path(__file__).resolve().parent.parent
CHAR_DATA_DIR = HERE / "Server" / "character_data"
DB_PATH = HERE / "Server" / "tftf_database.db"
BASIC_ABILITIES_JSON = HERE / "tools" / "basic_abilities.json"

WEBSITE_CHAR_DIR = Path(r"D:\#E\Personal\kmcbest.github.io\tftfr\data\characters")
WEBSITE_BASIC_JSON = Path(r"D:\#E\Personal\kmcbest.github.io\tftfr\data\basic_abilities.json")


def fetch_all_upstash_characters():
    print("1. Fetching all keys from Upstash KV...")
    req = urllib.request.Request(
        f"{UPSTASH_URL}/keys/tftf:char:*",
        headers={"Authorization": f"Bearer {WRITE_TOKEN}"}
    )
    with urllib.request.urlopen(req) as resp:
        keys = json.loads(resp.read().decode("utf-8")).get("result", [])

    print(f"   Found {len(keys)} keys in Upstash.")
    chunk_size = 25
    all_bots = {}
    for i in range(0, len(keys), chunk_size):
        chunk = keys[i:i + chunk_size]
        cmds = [["GET", k] for k in chunk]
        req = urllib.request.Request(
            f"{UPSTASH_URL}/pipeline",
            headers={"Authorization": f"Bearer {WRITE_TOKEN}", "Content-Type": "application/json"},
            data=json.dumps(cmds).encode("utf-8")
        )
        with urllib.request.urlopen(req) as resp:
            res_list = json.loads(resp.read().decode("utf-8"))
            for k, item in zip(chunk, res_list):
                val = item.get("result")
                if val:
                    bid = k.replace("tftf:char:", "")
                    if bid == "test":
                        continue
                    all_bots[bid] = json.loads(val) if isinstance(val, str) else val

    print(f"   Successfully fetched {len(all_bots)} characters from Upstash.")
    return all_bots


def sync_to_website_repo(all_bots):
    if not WEBSITE_CHAR_DIR.exists():
        print(f"[!] Website characters dir not found: {WEBSITE_CHAR_DIR}, skipping website JSON sync.")
        return
    print(f"2. Syncing {len(all_bots)} character JSONs to website repo: {WEBSITE_CHAR_DIR}...")
    count = 0
    for bid, bdata in all_bots.items():
        out_path = WEBSITE_CHAR_DIR / f"{bid}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(bdata, f, ensure_ascii=False, indent=2)
            f.write("\n")
        count += 1
    print(f"   Synced {count} characters to {WEBSITE_CHAR_DIR}")


def sync_to_server_character_data(all_bots):
    print(f"3. Syncing basic_abilities into Server/character_data/*.json...")
    updated_files = 0
    total_basics_count = 0

    # Build mapping for lookup
    for bid, bdata in all_bots.items():
        up_basics = [a for a in bdata.get("abilities", []) if a.get("category") == "basic"]
        clean_basics = []
        for a in up_basics:
            clean_basics.append({
                "title_zh": a.get("title_zh", "").strip(),
                "title_en": a.get("title_en", "").strip(),
                "desc_zh": a.get("desc_zh", "").strip(),
                "desc_en": a.get("desc_en", "").strip(),
                "pua_icon": a.get("pua_icon", "").strip()
            })

        # Possible target filenames
        target_stems = [bid]
        if bid == "elita_one_gs_kabam":
            target_stems.append("elita_one_gs")
        elif bid == "elita_one_gs":
            target_stems.append("elita_one_gs_kabam")

        for stem in target_stems:
            p = CHAR_DATA_DIR / f"{stem}.json"
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        cdata = json.load(f)
                    cdata["basic_abilities"] = clean_basics
                    with open(p, "w", encoding="utf-8") as f:
                        json.dump(cdata, f, ensure_ascii=False, indent=2)
                        f.write("\n")
                    updated_files += 1
                except Exception as e:
                    print(f"   [WARN] Failed to write {p.name}: {e}")

        total_basics_count += len(clean_basics)

    print(f"   Updated {updated_files} character_data JSON files (Total {total_basics_count} basic abilities).")


def sync_to_sqlite_database(all_bots):
    print(f"4. Syncing basic abilities to Server/tftf_database.db...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Delete existing basic category abilities
    cur.execute("DELETE FROM character_abilities WHERE category = 'basic'")
    deleted = cur.rowcount
    print(f"   Deleted {deleted} previous basic ability records.")

    cur.execute("SELECT id FROM character_abilities")
    used_ids = {r[0] for r in cur.fetchall()}

    inserted = 0
    for bid, bdata in all_bots.items():
        db_bid = "elita_one_gs" if bid == "elita_one_gs_kabam" else bid
        up_basics = [a for a in bdata.get("abilities", []) if a.get("category") == "basic"]
        for idx, a in enumerate(up_basics):
            aid = a.get("id")
            if aid is not None:
                try:
                    aid = int(aid)
                except Exception:
                    aid = None
            if aid is None or aid in used_ids:
                aid = None
            else:
                used_ids.add(aid)

            cat = "basic"
            tzh = a.get("title_zh", "").strip()
            ten = a.get("title_en", "").strip()
            dzh = a.get("desc_zh", "").strip()
            den = a.get("desc_en", "").strip()
            pua = a.get("pua_icon", "").strip()
            raw = a.get("raw_data_json", "")
            order = a.get("sort_order", 100 + idx)
            syn = json.dumps(a.get("synergy_bots", [])) if isinstance(a.get("synergy_bots"), list) else str(a.get("synergy_bots") or "[]")
            status = a.get("status", "implemented")

            if aid is not None:
                cur.execute("""
                    INSERT INTO character_abilities (
                        id, bot_id, category, title_zh, title_en, desc_zh, desc_en,
                        pua_icon, raw_data_json, sort_order, synergy_bots, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (aid, db_bid, cat, tzh, ten, dzh, den, pua, raw, order, syn, status))
            else:
                cur.execute("""
                    INSERT INTO character_abilities (
                        bot_id, category, title_zh, title_en, desc_zh, desc_en,
                        pua_icon, raw_data_json, sort_order, synergy_bots, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (db_bid, cat, tzh, ten, dzh, den, pua, raw, order, syn, status))
            inserted += 1

    conn.commit()
    conn.close()
    print(f"   Inserted {inserted} basic ability records into character_abilities table.")


def rebuild_basic_abilities_catalog(all_bots):
    print(f"5. Rebuilding tools/basic_abilities.json...")
    # Load canonical character metadata from DB
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT bot_id, name_zh, name_en, faction, class FROM characters ORDER BY name_zh")
    char_map = {}
    characters_all = []
    for r in cur.fetchall():
        info = {
            "bot_id": r[0],
            "name_zh": r[1] or r[0],
            "name_en": r[2] or r[0],
            "faction": r[3] or "",
            "class": r[4] or ""
        }
        char_map[r[0]] = info
        characters_all.append(info)
    conn.close()

    # Load existing catalog to preserve metadata (category, custom descriptions, id slug)
    existing_catalog = {}
    if BASIC_ABILITIES_JSON.exists():
        with open(BASIC_ABILITIES_JSON, "r", encoding="utf-8") as f:
            try:
                old_data = json.load(f)
                for ab in old_data.get("abilities", []):
                    existing_catalog[ab.get("name_zh")] = ab
            except Exception:
                pass

    # Group all Upstash basics by name_zh
    abilities_by_name = defaultdict(list)
    for bid, bdata in all_bots.items():
        db_bid = "elita_one_gs" if bid == "elita_one_gs_kabam" else bid
        up_basics = [a for a in bdata.get("abilities", []) if a.get("category") == "basic"]
        for a in up_basics:
            name_zh = a.get("title_zh", "").strip()
            if not name_zh:
                continue
            abilities_by_name[name_zh].append((db_bid, a))

    # Helper for pua char
    def get_pua_char(icon_hex):
        if not icon_hex:
            return ""
        try:
            val = int(icon_hex.replace("0x", "").strip(), 16)
            return chr(val)
        except Exception:
            return ""

    # Helper for ability slug
    def make_slug(name_en, name_zh):
        if name_en:
            slug = re.sub(r'[^a-zA-Z0-9]+', '_', name_en.lower()).strip('_')
            if slug:
                return slug
        import hashlib
        return "ab_" + hashlib.md5(name_zh.encode("utf-8")).hexdigest()[:8]

    # Category inference helper
    def infer_category(name_zh, desc_zh):
        text = f"{name_zh} {desc_zh}"
        if any(w in text for w in ["流血", "燃烧", "震击", "酸", "持续造成", "黑暗燃烧"]):
            return "持续伤害"
        if any(w in text for w in ["增益", "攻击", "暴击", "能量获取", "狂怒", "放大", "不可阻挡"]):
            return "增益"
        if any(w in text for w in ["破甲", "破盾", "减速", "能量燃烧", "能量流失", "能量锁定", "眩晕", "干扰", "封锁", "减益"]):
            return "减益"
        if any(w in text for w in ["护盾", "护甲", "规避", "格挡", "抗性", "保护", "吸收", "反击", "反伤"]):
            return "防御"
        if any(w in text for w in ["修复", "生命", "治疗", "传递"]):
            return "治疗"
        return "特殊能力"

    abilities_list = []
    for name_zh, occurrences in sorted(abilities_by_name.items()):
        # Check existing catalog
        existing = existing_catalog.get(name_zh, {})
        first_a = occurrences[0][1]

        name_en = existing.get("name_en") or first_a.get("title_en", "").strip()
        pua_icon = existing.get("pua_icon") or first_a.get("pua_icon", "").strip()
        pua_char = existing.get("pua_char") or get_pua_char(pua_icon)
        desc_zh = existing.get("desc_zh") or first_a.get("desc_zh", "").strip()
        desc_en = existing.get("desc_en") or first_a.get("desc_en", "").strip()
        cat = existing.get("category") or infer_category(name_zh, desc_zh)
        aid = existing.get("id") or make_slug(name_en, name_zh)

        # Build associated_bots
        seen_bots = set()
        associated_bots = []
        for db_bid, _ in occurrences:
            if db_bid not in seen_bots:
                seen_bots.add(db_bid)
                b_info = char_map.get(db_bid, {
                    "bot_id": db_bid,
                    "name_zh": db_bid,
                    "name_en": db_bid,
                    "faction": "",
                    "class": ""
                })
                associated_bots.append(b_info)

        # Sort associated_bots by name_zh
        associated_bots.sort(key=lambda x: x["name_zh"])

        abilities_list.append({
            "id": aid,
            "name_zh": name_zh,
            "name_en": name_en,
            "category": cat,
            "pua_icon": pua_icon,
            "pua_char": pua_char,
            "desc_zh": desc_zh,
            "desc_en": desc_en,
            "bot_count": len(associated_bots),
            "associated_bots": associated_bots
        })

    # Sort abilities by bot_count desc, then name_zh
    abilities_list.sort(key=lambda x: (-x["bot_count"], x["name_zh"]))

    catalog_data = {
        "meta": {
            "title": "TFTF Common Basic Abilities Catalog",
            "version": "2.1",
            "total_abilities": len(abilities_list),
            "total_characters": len(characters_all),
            "updated_at": datetime.now().strftime("%Y-%m-%d")
        },
        "characters_all": characters_all,
        "abilities": abilities_list
    }

    with open(BASIC_ABILITIES_JSON, "w", encoding="utf-8") as f:
        json.dump(catalog_data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"   Wrote {len(abilities_list)} abilities into {BASIC_ABILITIES_JSON}")

    if WEBSITE_BASIC_JSON.parent.exists():
        with open(WEBSITE_BASIC_JSON, "w", encoding="utf-8") as f:
            json.dump(catalog_data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"   Synced updated catalog to {WEBSITE_BASIC_JSON}")


def main():
    print("=== TFTF Upstash Basic Abilities Full Synchronizer ===")
    all_bots = fetch_all_upstash_characters()
    sync_to_website_repo(all_bots)
    sync_to_server_character_data(all_bots)
    sync_to_sqlite_database(all_bots)
    rebuild_basic_abilities_catalog(all_bots)
    print("\nData synchronization complete! Now regenerating game responses...")


if __name__ == "__main__":
    main()
